"""Construct two PUBLIC viewable BMP candidates on the runtime-selected iGPU."""
import os
from pathlib import Path
import struct
import time

from .files import DemoError, output, write_json

KERNEL = r"""
__kernel void paint(__global uchar *pixels, const uint palette) {
    uint i = (uint)get_global_id(0);
    uint x = i & 255u, y = i >> 8;
    pixels[3*i]   = (uchar)(x + (palette & 255u));
    pixels[3*i+1] = (uchar)(y + ((palette >> 8) & 255u));
    pixels[3*i+2] = (uchar)((x ^ y) + ((palette >> 16) & 255u));
}
"""


def create_images(folder):
    import numpy as np
    import pyopencl as cl
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=False)
    matches = [(p, d) for p in cl.get_platforms()
               for d in p.get_devices(device_type=cl.device_type.GPU)
               if d.host_unified_memory]
    if len(matches) != 1:
        raise DemoError("A unique runtime-observed unified-memory GPU is required; no silent fallback")
    platform, device = matches[0]
    ctx = cl.Context([device])
    queue = cl.CommandQueue(ctx, properties=cl.command_queue_properties.PROFILING_ENABLE)
    cache = folder / ".opencl-cache"
    cache.mkdir()
    program = cl.Program(ctx, KERNEL).build(cache_dir=str(cache))
    kernel = cl.Kernel(program, "paint")
    width = height = 256
    count = width * height * 3
    header = struct.pack("<2sIHHI", b"BM", 54 + count, 0, 0, 54)
    header += struct.pack("<IiiHHIIiiII", 40, width, height, 1, 24, 0, count, 2835, 2835, 0, 0)
    records = []
    for slot in range(2):
        palette = int.from_bytes(os.urandom(4), "little")
        host = np.empty(count, dtype=np.uint8)
        buffer = cl.Buffer(ctx, cl.mem_flags.WRITE_ONLY, count)
        start = time.perf_counter_ns()
        event = kernel(queue, (width * height,), None, buffer, np.uint32(palette))
        cl.enqueue_copy(queue, host, buffer, wait_for=[event]).wait()
        with output(folder / f"candidate-{slot}.bmp") as f:
            f.write(header)
            f.write(host.tobytes())
        records.append({"file": f"candidate-{slot}.bmp", "bytes": 54 + count,
                        "public_palette": palette, "gpu_kernel_ns": event.profile.end-event.profile.start,
                        "host_start_ns": start, "host_end_ns": time.perf_counter_ns(),
                        "device_to_host_bytes": count})
        buffer.release()
    value = {"classification": "PUBLIC_TEACHING_CANDIDATES_NO_INTENDED_MARKER",
             "device": {"name": device.name, "vendor": device.vendor, "vendor_id": device.vendor_id,
                        "driver": device.driver_version, "platform": platform.name,
                        "runtime_handle": int(device.int_ptr), "host_unified_memory": True},
             "records": records, "kernel": KERNEL,
             "utilization_target": [0.60, 0.70], "utilization_achieved": None,
             "private_gpu_operations": 0}
    write_json(folder / "IMAGE_ORIGIN.json", value)
    return value
