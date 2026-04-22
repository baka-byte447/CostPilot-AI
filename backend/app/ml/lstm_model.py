import numpy as np
import os


class LSTMForecaster:
    def __init__(self, hidden_size: int = 16, look_back: int = 20, lr: float = 0.005):
        self.H = hidden_size
        self.look_back = look_back
        self.lr = lr
        self.mean_ = 0.0
        self.std_ = 1.0
        self._init_weights()

    def _sigmoid(self, x):
        return 1.0 / (1.0 + np.exp(-np.clip(x, -10, 10)))

    def _init_weights(self):
        H = self.H
        D = H + 1
        s = 0.1
        self.Wf = np.random.randn(H, D) * s
        self.Wi = np.random.randn(H, D) * s
        self.Wg = np.random.randn(H, D) * s
        self.Wo = np.random.randn(H, D) * s
        self.bf = np.zeros(H)
        self.bi = np.zeros(H)
        self.bg = np.zeros(H)
        self.bo = np.zeros(H)
        self.Wy = np.random.randn(1, H) * s
        self.by = np.zeros(1)

    def _forward_sequence(self, x_seq):
        T = len(x_seq)
        h = np.zeros(self.H)
        c = np.zeros(self.H)
        hs, cs, fs, is_, gs, os_, xhs = [h.copy()], [c.copy()], [], [], [], [], []

        for t in range(T):
            xh = np.concatenate([[x_seq[t]], h])
            xhs.append(xh)
            f = self._sigmoid(self.Wf @ xh + self.bf)
            i = self._sigmoid(self.Wi @ xh + self.bi)
            g = np.tanh(self.Wg @ xh + self.bg)
            o = self._sigmoid(self.Wo @ xh + self.bo)
            c = f * c + i * g
            h = o * np.tanh(c)
            hs.append(h.copy()); cs.append(c.copy())
            fs.append(f); is_.append(i); gs.append(g); os_.append(o)

        return hs, cs, fs, is_, gs, os_, xhs

    def _make_sequences(self, data):
        X, Y = [], []
        for i in range(len(data) - self.look_back):
            X.append(data[i:i + self.look_back])
            Y.append(data[i + self.look_back])
        return np.array(X), np.array(Y)

    def fit(self, series, epochs: int = 30):
        data = np.array(series, dtype=float)
        self.mean_ = data.mean()
        self.std_ = data.std() + 1e-6
        data = (data - self.mean_) / self.std_

        X, Y = self._make_sequences(data)

        for _ in range(epochs):
            for x_seq, y_true in zip(X, Y):
                hs, cs, fs, is_, gs, os_, xhs = self._forward_sequence(x_seq)
                T = len(x_seq)

                y_pred = (self.Wy @ hs[-1] + self.by)[0]
                dy = 2.0 * (y_pred - y_true)

                dWy = dy * hs[-1].reshape(1, -1)
                dby = np.array([dy])
                dh  = (self.Wy.T * dy).reshape(-1)
                dc  = np.zeros(self.H)

                dWf = np.zeros_like(self.Wf); dWi = np.zeros_like(self.Wi)
                dWg = np.zeros_like(self.Wg); dWo = np.zeros_like(self.Wo)
                dbf = np.zeros(self.H); dbi = np.zeros(self.H)
                dbg = np.zeros(self.H); dbo = np.zeros(self.H)

                for t in reversed(range(T)):
                    c_t    = cs[t + 1]
                    c_prev = cs[t]
                    f_t = fs[t]; i_t = is_[t]; g_t = gs[t]; o_t = os_[t]

                    tanh_c = np.tanh(c_t)
                    do = dh * tanh_c
                    dc += dh * o_t * (1.0 - tanh_c ** 2)
                    df = dc * c_prev
                    di = dc * g_t
                    dg = dc * i_t
                    dc  = dc * f_t

                    do_ = do * o_t * (1.0 - o_t)
                    df_ = df * f_t * (1.0 - f_t)
                    di_ = di * i_t * (1.0 - i_t)
                    dg_ = dg * (1.0 - g_t ** 2)

                    xh = xhs[t]
                    dWf += np.outer(df_, xh); dWi += np.outer(di_, xh)
                    dWg += np.outer(dg_, xh); dWo += np.outer(do_, xh)
                    dbf += df_; dbi += di_; dbg += dg_; dbo += do_

                    dxh = (self.Wf.T @ df_ + self.Wi.T @ di_ +
                           self.Wg.T @ dg_ + self.Wo.T @ do_)
                    dh = dxh[1:]

                clip = 1.0
                for g in [dWf, dWi, dWg, dWo, dbf, dbi, dbg, dbo, dWy, dby]:
                    np.clip(g, -clip, clip, out=g)

                self.Wf -= self.lr * dWf; self.Wi -= self.lr * dWi
                self.Wg -= self.lr * dWg; self.Wo -= self.lr * dWo
                self.bf -= self.lr * dbf; self.bi -= self.lr * dbi
                self.bg -= self.lr * dbg; self.bo -= self.lr * dbo
                self.Wy -= self.lr * dWy; self.by -= self.lr * dby

    def _predict_one(self, window):
        T = len(window)
        h = np.zeros(self.H)
        c = np.zeros(self.H)
        for t in range(T):
            xh = np.concatenate([[window[t]], h])
            f = self._sigmoid(self.Wf @ xh + self.bf)
            i = self._sigmoid(self.Wi @ xh + self.bi)
            g = np.tanh(self.Wg @ xh + self.bg)
            o = self._sigmoid(self.Wo @ xh + self.bo)
            c = f * c + i * g
            h = o * np.tanh(c)
        return float((self.Wy @ h + self.by)[0])

    def predict(self, series, steps: int = 6):
        data = np.array(series, dtype=float)
        data_norm = (data - self.mean_) / self.std_
        window = list(data_norm[-self.look_back:])
        preds = []
        for _ in range(steps):
            y_norm = self._predict_one(np.array(window))
            preds.append(y_norm * self.std_ + self.mean_)
            window.append(y_norm)
            if len(window) > self.look_back:
                window = window[-self.look_back:]
        return preds

    def save(self, path: str):
        os.makedirs(os.path.dirname(path) if os.path.dirname(path) else ".", exist_ok=True)
        np.savez(
            path,
            Wf=self.Wf, Wi=self.Wi, Wg=self.Wg, Wo=self.Wo,
            bf=self.bf, bi=self.bi, bg=self.bg, bo=self.bo,
            Wy=self.Wy, by=self.by,
            meta=np.array([self.mean_, self.std_, float(self.H), float(self.look_back)])
        )

    @classmethod
    def load(cls, path: str):
        d = np.load(path + ".npz")
        meta = d["meta"]
        obj = cls(hidden_size=int(meta[2]), look_back=int(meta[3]))
        obj.mean_ = float(meta[0])
        obj.std_  = float(meta[1])
        obj.Wf = d["Wf"]; obj.Wi = d["Wi"]
        obj.Wg = d["Wg"]; obj.Wo = d["Wo"]
        obj.bf = d["bf"]; obj.bi = d["bi"]
        obj.bg = d["bg"]; obj.bo = d["bo"]
        obj.Wy = d["Wy"]; obj.by = d["by"]
        return obj
