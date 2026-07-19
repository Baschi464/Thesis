"""
models.py -- shared ForwardModel API + GP / Linear / MLP(scaffold)
(gp_code_handoff.md SS5).

  class ForwardModel:
      def fit(self, X, dZ): ...
      def predict(self, X): ...
      def predict_with_std(self, X): ...

X columns = [z_t..., u_t, dir_t] (vector-ready: z may be >1 column; u_t and
dir_t are always the last two columns). dZ is (N, k), k = state dimension.
"""

from typing import Optional

import numpy as np
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import RBF, ConstantKernel, Matern, WhiteKernel
from sklearn.linear_model import LinearRegression

from .data import Standardizer


def _build_kernel(kernel_name: str, n_dims: int, ard: bool = True):
    length_scale = np.ones(n_dims) if ard else 1.0
    if kernel_name == "matern52_ard":
        base = Matern(length_scale=length_scale, nu=2.5)
    elif kernel_name == "matern32_ard":
        base = Matern(length_scale=length_scale, nu=1.5)
    elif kernel_name == "rbf_ard":
        base = RBF(length_scale=length_scale)
    else:
        raise ValueError(f"unknown kernel {kernel_name!r} "
                          "(expected matern52_ard | matern32_ard | rbf_ard)")
    return ConstantKernel(1.0, (1e-3, 1e3)) * base + WhiteKernel(1e-3, (1e-8, 1e1))


class GPForwardModel:
    """Variant B1 (mode="delta": target=Δz) or Variant A's second stage
    (mode="residual": target=Δz − Δz_prior). One independent GP per output
    dimension (vector-ready).

    For mode="residual", the caller MUST pass dZ_prior explicitly to both
    fit() and predict_with_std() -- computed via prior.PriorModel.predict_delta
    using each row's REAL dt (dt isn't one of this model's input columns
    [z_t, u_t, dir_t], so it can't be reconstructed here; see evaluate.py/
    cli.py for where dZ_prior is actually computed from the dataframe).
    """

    def __init__(self, kernel: str = "matern52_ard", ard: bool = True,
                 normalize_y: bool = True, standardize_x: bool = True,
                 n_restarts_optimizer: int = 3, alpha: float = 1e-10,
                 mode: str = "delta", random_state: int = 0):
        self.kernel_name = kernel
        self.ard = ard
        self.normalize_y = normalize_y
        self.standardize_x = standardize_x
        self.n_restarts_optimizer = n_restarts_optimizer
        self.alpha = alpha
        self.mode = mode
        self.random_state = random_state

        self._standardizer: Optional[Standardizer] = None
        self._gps = []
        self.n_outputs_ = None
        self.n_state_dims_ = None  # inferred at fit time: X.shape[1] - 2 (u_t, dir_t)

    def fit(self, X, dZ, dZ_prior: Optional[np.ndarray] = None):
        X = np.asarray(X, dtype=float)
        dZ = np.asarray(dZ, dtype=float)
        if dZ.ndim == 1:
            dZ = dZ.reshape(-1, 1)
        self.n_outputs_ = dZ.shape[1]
        self.n_state_dims_ = X.shape[1] - 2

        if self.mode == "residual":
            if dZ_prior is None:
                raise ValueError("mode='residual' requires dZ_prior (see class docstring)")
            dZ_prior = np.asarray(dZ_prior, dtype=float).reshape(dZ.shape)
            target = dZ - dZ_prior
        else:
            target = dZ

        self._standardizer = Standardizer()
        Xs = self._standardizer.fit_transform(X) if self.standardize_x else X

        self._gps = []
        for k in range(self.n_outputs_):
            kernel = _build_kernel(self.kernel_name, Xs.shape[1], self.ard)
            gp = GaussianProcessRegressor(
                kernel=kernel, normalize_y=self.normalize_y,
                n_restarts_optimizer=self.n_restarts_optimizer,
                alpha=self.alpha, random_state=self.random_state,
            )
            gp.fit(Xs, target[:, k])
            self._gps.append(gp)
        return self

    def lengthscales(self):
        """Learned ARD lengthscale per input dim, per output GP -- for the
        deadzone/ARD discussion (gp_handoff.md kernel-choice rationale)."""
        out = []
        for gp in self._gps:
            k = gp.kernel_
            # kernel_ = ConstantKernel * Matern/RBF + WhiteKernel
            base = k.k1.k2
            ls = np.atleast_1d(base.length_scale)
            out.append(ls)
        return out

    def predict_with_std(self, X, dZ_prior: Optional[np.ndarray] = None):
        X = np.asarray(X, dtype=float)
        Xs = self._standardizer.transform(X) if self.standardize_x else X
        means, stds = [], []
        for gp in self._gps:
            m, s = gp.predict(Xs, return_std=True)
            means.append(m)
            stds.append(s)
        mean = np.column_stack(means)
        std = np.column_stack(stds)
        if self.mode == "residual":
            if dZ_prior is None:
                raise ValueError("mode='residual' requires dZ_prior (see class docstring)")
            mean = mean + np.asarray(dZ_prior, dtype=float).reshape(mean.shape)
        return mean, std

    def predict(self, X, dZ_prior: Optional[np.ndarray] = None):
        mean, _ = self.predict_with_std(X, dZ_prior=dZ_prior)
        return mean


class PriorPlusGP:
    """Bundles a fitted prior.PriorModel + a residual-mode GPForwardModel
    into one ForwardModel-compatible predictor (Variant A deployed as a
    single unit) -- e.g. for models.rollout()/compose.py, which expect a
    plain predict_with_std(X) with no separate dt argument.

    `dt` is bound at construction (a single representative value, e.g. the
    synthetic generator's fixed frame dt) since rollout/composition here
    always operate on constant-dt sequences. For one-step evaluation on
    real per-row dt values, call GPForwardModel.predict_with_std(X,
    dZ_prior=...) directly with dZ_prior computed from each row's actual
    dt instead of going through this adapter (see evaluate.py).
    """

    def __init__(self, prior_model, gp_residual: GPForwardModel, tau: float, dt: float):
        self.prior_model = prior_model
        self.gp_residual = gp_residual
        self.tau = tau
        self.dt = dt

    def _dZ_prior(self, X):
        n_state = self.gp_residual.n_state_dims_
        z_t = X[:, :n_state]
        u_t = X[:, n_state]
        dt_arr = np.full(len(X), self.dt)
        return self.prior_model.predict_delta(z_t[:, 0], u_t, dt_arr, self.tau).reshape(-1, 1)

    def predict_with_std(self, X):
        X = np.asarray(X, dtype=float)
        dZ_prior = self._dZ_prior(X)
        return self.gp_residual.predict_with_std(X, dZ_prior=dZ_prior)

    def predict(self, X):
        mean, _ = self.predict_with_std(X)
        return mean


class LinearForwardModel:
    """Variant B2: least squares on [z_t, u_t, dir_t]. No uncertainty."""

    def __init__(self, fit_intercept: bool = True):
        self.fit_intercept = fit_intercept
        self._models = []
        self.n_outputs_ = None

    def fit(self, X, dZ):
        X = np.asarray(X, dtype=float)
        dZ = np.asarray(dZ, dtype=float)
        if dZ.ndim == 1:
            dZ = dZ.reshape(-1, 1)
        self.n_outputs_ = dZ.shape[1]
        self._models = []
        for k in range(self.n_outputs_):
            m = LinearRegression(fit_intercept=self.fit_intercept)
            m.fit(X, dZ[:, k])
            self._models.append(m)
        return self

    def predict(self, X):
        X = np.asarray(X, dtype=float)
        return np.column_stack([m.predict(X) for m in self._models])

    def predict_with_std(self, X):
        return self.predict(X), None


class MLPForwardModel:
    """Variant B3 -- SCAFFOLD ONLY (gp_code_handoff.md SS5: 'do not invest
    heavily'). Small sklearn MLPRegressor; optional; no uncertainty.
    """

    def __init__(self, hidden_layer_sizes=(16, 16), max_iter: int = 2000,
                 random_state: int = 0):
        from sklearn.neural_network import MLPRegressor
        self.hidden_layer_sizes = tuple(hidden_layer_sizes)
        self.max_iter = max_iter
        self.random_state = random_state
        self._MLPRegressor = MLPRegressor
        self._models = []
        self._standardizer: Optional[Standardizer] = None
        self.n_outputs_ = None

    def fit(self, X, dZ):
        X = np.asarray(X, dtype=float)
        dZ = np.asarray(dZ, dtype=float)
        if dZ.ndim == 1:
            dZ = dZ.reshape(-1, 1)
        self.n_outputs_ = dZ.shape[1]
        self._standardizer = Standardizer()
        Xs = self._standardizer.fit_transform(X)
        self._models = []
        for k in range(self.n_outputs_):
            m = self._MLPRegressor(hidden_layer_sizes=self.hidden_layer_sizes,
                                    max_iter=self.max_iter, random_state=self.random_state)
            m.fit(Xs, dZ[:, k])
            self._models.append(m)
        return self

    def predict(self, X):
        X = np.asarray(X, dtype=float)
        Xs = self._standardizer.transform(X)
        return np.column_stack([m.predict(Xs) for m in self._models])

    def predict_with_std(self, X):
        return self.predict(X), None


def rollout(model, z0: np.ndarray, u_seq: np.ndarray, dir_seq: np.ndarray,
            horizon: Optional[int] = None):
    """Multi-step rollout: feed predictions back as the next z_t. Returns
    (z_traj, std_traj) with shape (horizon+1, k) each (std_traj is None for
    non-probabilistic models).

    GP variance propagation approximation (gp_code_handoff.md SS5, "for GP,
    propagate variance approximately along the rollout (document the
    approximation)"): variance is accumulated ADDITIVELY step to step
    (var_t = var_{t-1} + predicted_var_t), i.e. treating each step's
    predictive variance as independent of prior rollout uncertainty. This
    ignores that feeding an uncertain z_t back into the GP should itself
    widen that step's predictive variance (a proper treatment needs moment
    matching or sampling); the additive approximation is a cheap, honest
    upper-bound-ish proxy, not an exact posterior propagation.
    """
    n = len(u_seq) if horizon is None else min(horizon, len(u_seq))
    k = np.atleast_1d(z0).shape[0]
    z_traj = np.zeros((n + 1, k))
    z_traj[0] = z0
    has_std = hasattr(model, "predict_with_std")
    std_traj = np.zeros((n + 1, k)) if has_std else None

    z = np.array(z0, dtype=float).reshape(1, -1)
    running_var = np.zeros((1, k))
    for t in range(n):
        X = np.column_stack([z, np.array([[u_seq[t]]]), np.array([[dir_seq[t]]])])
        if has_std:
            mean, std = model.predict_with_std(X)
            running_var = running_var + std ** 2
            std_traj[t + 1] = np.sqrt(running_var)[0]
        else:
            mean = model.predict(X)
        z = z + mean
        z_traj[t + 1] = z[0]

    return z_traj, std_traj
