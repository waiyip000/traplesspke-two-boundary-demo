"""Optional iGPU producer for PUBLIC teaching files, never crypto randomness."""
import json
import os
from pathlib import Path
import time

from .files import DemoError, output, write_json
from .paths import plain, vacant

KERNEL = r"""
__kernel void teaching_bytes(__global uint *out, const uint seed) {
    uint x = (uint)get_global_id(0) ^ seed;
    x ^= x << 13; x ^= x >> 17; x ^= x << 5;
    out[get_global_id(0)] = x;
}
"""


def create_public_inputs(folder):
    import numpy as np
    import pyopencl as cl
    folder = plain(folder)
    if not folder.is_dir():
        raise DemoError("Public input producer requires an existing ordinary folder")
    for name in (".opencl-cache","candidate-0.bin","candidate-1.bin","INPUT_ORIGIN.json"):
        vacant(folder/name)
    start = time.perf_counter_ns()
    devices = []
    for platform in cl.get_platforms():
        for device in platform.get_devices(device_type=cl.device_type.GPU):
            if device.host_unified_memory:
                devices.append((platform, device))
    if len(devices) != 1:
        raise DemoError("Exactly one runtime-observed unified-memory hardware GPU is required; no silent CPU fallback")
    platform, device = devices[0]
    identity = {"platform": platform.name, "platform_version": platform.version,
                "name": device.name, "vendor": device.vendor, "vendor_id": device.vendor_id,
                "driver": device.driver_version, "host_unified_memory": bool(device.host_unified_memory),
                "runtime_handle": int(device.int_ptr), "compute_units": device.max_compute_units,
                "selector": "Unique GPU enumerated in this OpenCL invocation with host_unified_memory=true"}
    context = cl.Context([device])
    queue = cl.CommandQueue(context, properties=cl.command_queue_properties.PROFILING_ENABLE)
    cache = folder / ".opencl-cache"
    cache.mkdir()
    program = cl.Program(context, KERNEL).build(cache_dir=str(cache))
    kernel = cl.Kernel(program, "teaching_bytes")
    records = []
    # Two small files are sufficient for the walkthrough; no utilization padding.
    words = 32768
    for slot in range(2):
        seed = int.from_bytes(os.urandom(4), "little")
        host = np.empty(words, dtype=np.uint32)
        buffer = cl.Buffer(context, cl.mem_flags.WRITE_ONLY, host.nbytes)
        event = kernel(queue, (words,), None, buffer, np.uint32(seed))
        copy_event = cl.enqueue_copy(queue, host, buffer, wait_for=[event])
        copy_event.wait()
        name = f"candidate-{slot}.bin"
        with output(folder / name) as f:
            f.write(host.astype("<u4", copy=False).tobytes())
        records.append({"file": name, "public_seed": seed, "bytes": host.nbytes,
                        "kernel_ns": event.profile.end - event.profile.start,
                        "device_to_host_bytes": host.nbytes})
        buffer.release()
    value = {"classification": "PUBLIC_SYNTHETIC_TEACHING_INPUTS", "device": identity,
             "records": records, "kernel_source": KERNEL,
             "start_host_ns": start, "end_host_ns": time.perf_counter_ns(),
             "not_cryptographic_randomness": True, "utilization_target": [0.60, 0.70],
             "utilization_achieved": None,
             "limit": "Finite useful input generation; no utilization filler or private GPU operation"}
    write_json(folder / "INPUT_ORIGIN.json", value)
    return value
