"""Optional PyTorch device smoke check; the scientific examples use NumPy/CPU."""

import importlib.util


def device_report(requested: str = "auto") -> dict:
    if requested not in {"auto", "cpu", "mps", "cuda"}:
        raise ValueError("Device must be auto, cpu, mps, or cuda.")
    report = {"example_backend": "numpy/cpu", "requested_torch_device": requested}
    if importlib.util.find_spec("torch") is None:
        if requested in {"mps", "cuda"}:
            raise ValueError("PyTorch is not installed; select the appropriate optional extra.")
        return {**report, "torch_installed": False, "torch_device": None}
    import torch

    available = {
        "cpu": True,
        "cuda": torch.cuda.is_available(),
        "mps": torch.backends.mps.is_available(),
    }
    selected = (
        next(name for name in ("cuda", "mps", "cpu") if available[name])
        if requested == "auto"
        else requested
    )
    if not available[selected]:
        raise ValueError(f"Requested {selected} is unavailable; no implicit CPU fallback.")
    # A successful allocation alone is insufficient: perform and verify an operation.
    values = torch.arange(16, dtype=torch.float32, device=selected).reshape(4, 4)
    result = (values @ values.T).cpu()
    expected = torch.arange(16, dtype=torch.float32).reshape(4, 4)
    if not torch.allclose(result, expected @ expected.T):
        raise RuntimeError("Device smoke check produced an unexpected result.")
    return {
        **report,
        "torch_installed": True,
        "torch_version": torch.__version__,
        "available": available,
        "torch_device": selected,
        "smoke_check": "passed",
    }
