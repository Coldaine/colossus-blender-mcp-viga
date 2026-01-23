"""
GPU Configuration Module for Blender Rendering
Supports RTX 3090 and RTX 5090 with optimized settings
"""

from dataclasses import dataclass
from typing import Literal
from enum import Enum


class GPUModel(Enum):
    """Supported GPU models"""
    RTX_3090 = "3090"
    RTX_5090 = "5090"
    AUTO = "auto"


@dataclass
class GPUSpecs:
    """GPU hardware specifications"""
    model: str
    vram_gb: int
    cuda_cores: int
    tensor_cores: int
    memory_bandwidth_gbps: float
    max_tile_size: int
    recommended_samples: int


# GPU Specifications Database
GPU_SPECS = {
    GPUModel.RTX_3090: GPUSpecs(
        model="RTX 3090",
        vram_gb=24,
        cuda_cores=10496,
        tensor_cores=328,
        memory_bandwidth_gbps=936,
        max_tile_size=256,
        recommended_samples=128
    ),
    GPUModel.RTX_5090: GPUSpecs(
        model="RTX 5090",
        vram_gb=32,
        cuda_cores=21760,  # Estimated
        tensor_cores=680,   # Estimated
        memory_bandwidth_gbps=1400,  # GDDR7
        max_tile_size=512,
        recommended_samples=256
    )
}


@dataclass
class RenderSettings:
    """Blender Cycles render settings"""
    # Device
    device: Literal["GPU", "CPU"] = "GPU"
    compute_device_type: Literal["CUDA", "OPTIX", "HIP", "METAL"] = "CUDA"

    # Sampling
    samples: int = 128
    adaptive_sampling: bool = True
    adaptive_threshold: float = 0.01
    denoising: bool = True

    # Tiles
    tile_size: int = 256
    tile_x: int = 256
    tile_y: int = 256

    # Performance
    use_gpu_memory_limit: bool = True
    gpu_memory_limit_mb: int = 20480  # 20GB (leave headroom)

    # Quality
    max_subdivisions: int = 2
    use_simplify: bool = True
    simplify_subdivision: int = 2

    # Volumetrics & Advanced
    volume_bounces: int = 2
    subsurface_samples: int = 2

    # Render resolution
    resolution_x: int = 1920
    resolution_y: int = 1080
    resolution_percentage: int = 100


class GPUConfigurator:
    """Configure Blender for optimal GPU rendering"""

    def __init__(self, gpu_model: GPUModel = GPUModel.RTX_3090):
        self.gpu_model = gpu_model
        self.specs = GPU_SPECS[gpu_model]

    def get_optimal_settings(
        self,
        quality: Literal["preview", "production", "final"] = "preview"
    ) -> RenderSettings:
        """
        Get optimal render settings for GPU and quality level

        Args:
            quality:
                - "preview": Fast iteration, lower quality
                - "production": Balanced quality/speed
                - "final": Maximum quality
        """
        if self.gpu_model == GPUModel.RTX_3090:
            return self._get_3090_settings(quality)
        elif self.gpu_model == GPUModel.RTX_5090:
            return self._get_5090_settings(quality)
        else:
            return self._get_fallback_settings(quality)

    def _get_3090_settings(self, quality: str) -> RenderSettings:
        """RTX 3090 optimized settings"""

        quality_profiles = {
            "preview": RenderSettings(
                device="GPU",
                compute_device_type="CUDA",
                samples=64,
                adaptive_sampling=True,
                adaptive_threshold=0.02,
                denoising=True,
                tile_size=256,
                tile_x=256,
                tile_y=256,
                use_gpu_memory_limit=True,
                gpu_memory_limit_mb=20480,  # Leave 4GB headroom
                max_subdivisions=1,
                use_simplify=True,
                simplify_subdivision=1,
                volume_bounces=1,
                subsurface_samples=1,
                resolution_percentage=50
            ),
            "production": RenderSettings(
                device="GPU",
                compute_device_type="CUDA",
                samples=128,
                adaptive_sampling=True,
                adaptive_threshold=0.01,
                denoising=True,
                tile_size=256,
                tile_x=256,
                tile_y=256,
                use_gpu_memory_limit=True,
                gpu_memory_limit_mb=20480,
                max_subdivisions=2,
                use_simplify=True,
                simplify_subdivision=2,
                volume_bounces=2,
                subsurface_samples=2,
                resolution_percentage=100
            ),
            "final": RenderSettings(
                device="GPU",
                compute_device_type="CUDA",
                samples=256,
                adaptive_sampling=True,
                adaptive_threshold=0.005,
                denoising=True,
                tile_size=256,
                tile_x=256,
                tile_y=256,
                use_gpu_memory_limit=True,
                gpu_memory_limit_mb=20480,
                max_subdivisions=3,
                use_simplify=False,
                simplify_subdivision=3,
                volume_bounces=4,
                subsurface_samples=3,
                resolution_percentage=100
            )
        }

        return quality_profiles.get(quality, quality_profiles["production"])

    def _get_5090_settings(self, quality: str) -> RenderSettings:
        """RTX 5090 optimized settings (more aggressive)"""

        quality_profiles = {
            "preview": RenderSettings(
                device="GPU",
                compute_device_type="CUDA",
                samples=128,
                adaptive_sampling=True,
                adaptive_threshold=0.01,
                denoising=True,
                tile_size=512,
                tile_x=512,
                tile_y=512,
                use_gpu_memory_limit=True,
                gpu_memory_limit_mb=28672,  # Leave 3.5GB headroom
                max_subdivisions=2,
                use_simplify=True,
                simplify_subdivision=2,
                volume_bounces=2,
                subsurface_samples=2,
                resolution_percentage=75
            ),
            "production": RenderSettings(
                device="GPU",
                compute_device_type="CUDA",
                samples=256,
                adaptive_sampling=True,
                adaptive_threshold=0.005,
                denoising=True,
                tile_size=512,
                tile_x=512,
                tile_y=512,
                use_gpu_memory_limit=True,
                gpu_memory_limit_mb=28672,
                max_subdivisions=4,
                use_simplify=False,
                simplify_subdivision=3,
                volume_bounces=4,
                subsurface_samples=3,
                resolution_percentage=100
            ),
            "final": RenderSettings(
                device="GPU",
                compute_device_type="CUDA",
                samples=512,
                adaptive_sampling=True,
                adaptive_threshold=0.001,
                denoising=True,
                tile_size=512,
                tile_x=512,
                tile_y=512,
                use_gpu_memory_limit=True,
                gpu_memory_limit_mb=28672,
                max_subdivisions=6,
                use_simplify=False,
                simplify_subdivision=4,
                volume_bounces=8,
                subsurface_samples=4,
                resolution_percentage=100
            )
        }

        return quality_profiles.get(quality, quality_profiles["production"])

    def _get_fallback_settings(self, quality: str) -> RenderSettings:
        """Conservative fallback settings"""
        return RenderSettings(
            device="GPU",
            compute_device_type="CUDA",
            samples=64,
            adaptive_sampling=True,
            adaptive_threshold=0.02,
            tile_size=128,
            tile_x=128,
            tile_y=128,
            max_subdivisions=1,
            use_simplify=True
        )

    def generate_blender_code(self, quality: str = "production") -> str:
        """
        Generate Python code to apply settings in Blender

        Returns:
            Executable Python code for Blender
        """
        settings = self.get_optimal_settings(quality)

        code = f'''
import bpy

def configure_gpu_{self.gpu_model.value}():
    """Configure Blender for {self.specs.model} ({quality} quality)"""

    # Enable GPU compute
    prefs = bpy.context.preferences.addons['cycles'].preferences
    prefs.compute_device_type = '{settings.compute_device_type}'

    # Enable all GPU devices
    prefs.get_devices()
    for device in prefs.devices:
        if device.type == '{settings.compute_device_type}':
            device.use = True
            print(f"Enabled device: {{device.name}}")

    # Scene settings
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    scene.cycles.device = '{settings.device}'

    # Sampling
    scene.cycles.samples = {settings.samples}
    scene.cycles.use_adaptive_sampling = {settings.adaptive_sampling}
    scene.cycles.adaptive_threshold = {settings.adaptive_threshold}
    scene.cycles.use_denoising = {settings.denoising}

    # Tile settings
    scene.cycles.tile_size = {settings.tile_size}
    scene.render.tile_x = {settings.tile_x}
    scene.render.tile_y = {settings.tile_y}

    # Subdivision
    scene.cycles.max_subdivisions = {settings.max_subdivisions}

    # Simplification
    scene.render.use_simplify = {settings.use_simplify}
    scene.render.simplify_subdivision = {settings.simplify_subdivision}

    # Volumetrics & SSS
    scene.cycles.volume_bounces = {settings.volume_bounces}
    scene.cycles.subsurface_samples = {settings.subsurface_samples}

    # Resolution
    scene.render.resolution_x = {settings.resolution_x}
    scene.render.resolution_y = {settings.resolution_y}
    scene.render.resolution_percentage = {settings.resolution_percentage}

    print(f"GPU configured: {self.specs.model} - {quality} quality")
    print(f"Samples: {settings.samples}, Tile: {settings.tile_size}x{settings.tile_size}")

    return {{
        "status": "success",
        "gpu_model": "{self.specs.model}",
        "quality": "{quality}",
        "samples": {settings.samples},
        "tile_size": {settings.tile_size},
        "vram_limit_mb": {settings.gpu_memory_limit_mb}
    }}

# Execute configuration
result = configure_gpu_{self.gpu_model.value}()
'''
        return code


def generate_gpu_benchmark_code() -> str:
    """Generate code to benchmark GPU performance in Blender"""

    code = '''
import bpy
import time
import json

def benchmark_gpu():
    """Benchmark GPU render performance"""

    # Create simple test scene
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()

    bpy.ops.mesh.primitive_uv_sphere_add(location=(0, 0, 1), subdivisions=5)

    # Add light
    light_data = bpy.data.lights.new(name="Sun", type='SUN')
    light_obj = bpy.data.objects.new(name="Sun", object_data=light_data)
    bpy.context.scene.collection.objects.link(light_obj)

    # Configure for benchmark
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'GPU'
    scene.cycles.samples = 128
    scene.render.resolution_x = 1920
    scene.render.resolution_y = 1080

    # Render and time it
    start_time = time.time()
    bpy.ops.render.render(write_still=False)
    render_time = time.time() - start_time

    return {
        "status": "success",
        "render_time_seconds": render_time,
        "samples": 128,
        "resolution": "1920x1080",
        "samples_per_second": 128 / render_time
    }

result = benchmark_gpu()
print(json.dumps(result))
'''
    return code


# Convenience functions
def get_gpu_config(gpu_model: str = "3090") -> GPUConfigurator:
    """Get GPU configurator for model"""
    model_map = {
        "3090": GPUModel.RTX_3090,
        "5090": GPUModel.RTX_5090
    }
    return GPUConfigurator(model_map.get(gpu_model, GPUModel.RTX_3090))


def compare_gpus():
    """Compare 3090 vs 5090 specifications"""
    specs_3090 = GPU_SPECS[GPUModel.RTX_3090]
    specs_5090 = GPU_SPECS[GPUModel.RTX_5090]

    print("=== GPU Comparison ===")
    print(f"\nRTX 3090:")
    print(f"  VRAM: {specs_3090.vram_gb}GB")
    print(f"  CUDA Cores: {specs_3090.cuda_cores}")
    print(f"  Max Tile: {specs_3090.max_tile_size}")
    print(f"  Recommended Samples: {specs_3090.recommended_samples}")

    print(f"\nRTX 5090:")
    print(f"  VRAM: {specs_5090.vram_gb}GB (+{specs_5090.vram_gb - specs_3090.vram_gb}GB)")
    print(f"  CUDA Cores: {specs_5090.cuda_cores} ({specs_5090.cuda_cores / specs_3090.cuda_cores:.1f}x)")
    print(f"  Max Tile: {specs_5090.max_tile_size} ({specs_5090.max_tile_size / specs_3090.max_tile_size:.1f}x)")
    print(f"  Recommended Samples: {specs_5090.recommended_samples} ({specs_5090.recommended_samples / specs_3090.recommended_samples:.1f}x)")

    print(f"\nPerformance Improvement: ~2.0x faster rendering")
    print(f"Memory Improvement: {((specs_5090.vram_gb - specs_3090.vram_gb) / specs_3090.vram_gb * 100):.0f}% more VRAM")
