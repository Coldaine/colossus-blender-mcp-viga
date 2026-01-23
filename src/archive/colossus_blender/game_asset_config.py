"""
Game Asset Configuration Profiles
Defines quality settings, polygon budgets, and export formats for different game engines
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from enum import Enum


class GameEngine(Enum):
    """Supported game engines and asset stores"""
    WAR_THUNDER = "war_thunder"
    WORLD_OF_WARSHIPS = "world_of_warships"
    UNITY = "unity"
    UNREAL = "unreal"
    ASSET_STORE = "asset_store"
    CUSTOM = "custom"


class ExportFormat(Enum):
    """Supported 3D file formats"""
    FBX = "fbx"
    GLTF = "gltf"
    GLB = "glb"
    OBJ = "obj"
    BLEND = "blend"


@dataclass
class LODLevel:
    """Level of Detail configuration"""
    name: str
    max_triangles: int
    reduction_ratio: float  # Relative to LOD0
    distance_min: float  # Meters
    distance_max: float  # Meters
    description: str = ""


@dataclass
class TextureSettings:
    """Texture resolution and format settings"""
    albedo_size: int = 4096
    normal_size: int = 4096
    roughness_size: int = 2048
    metallic_size: int = 2048
    ao_size: int = 2048  # Ambient occlusion
    format: str = "PNG"  # PNG, TGA, JPEG
    compression: bool = True


@dataclass
class MaterialProfile:
    """PBR material configuration for naval vessels"""
    name: str
    base_color: tuple = (0.29, 0.33, 0.41, 1.0)  # Default: naval gray
    metallic: float = 0.0
    roughness: float = 0.5
    description: str = ""


# Predefined material profiles for battleships
NAVAL_MATERIALS = {
    "steel_hull": MaterialProfile(
        name="Naval Steel Hull",
        base_color=(0.29, 0.33, 0.41, 1.0),  # Gray-blue
        metallic=1.0,
        roughness=0.4,
        description="Painted steel hull exterior"
    ),
    "deck_wood": MaterialProfile(
        name="Teak Deck Wood",
        base_color=(0.55, 0.45, 0.34, 1.0),  # Brownish teak
        metallic=0.0,
        roughness=0.8,
        description="Weathered teak deck planking"
    ),
    "rust_weathering": MaterialProfile(
        name="Rust and Weathering",
        base_color=(0.52, 0.31, 0.18, 1.0),  # Rust orange-brown
        metallic=0.3,
        roughness=0.9,
        description="Rust and corrosion effects"
    ),
    "superstructure": MaterialProfile(
        name="Superstructure Gray",
        base_color=(0.60, 0.60, 0.62, 1.0),  # Lighter gray
        metallic=0.8,
        roughness=0.3,
        description="Superstructure and bridge structures"
    ),
    "gun_metal": MaterialProfile(
        name="Gun Barrel Metal",
        base_color=(0.18, 0.18, 0.20, 1.0),  # Dark gunmetal
        metallic=1.0,
        roughness=0.2,
        description="Gun barrels and turrets"
    )
}


@dataclass
class GameAssetProfile:
    """Complete asset profile for a specific game/platform"""
    name: str
    engine: GameEngine

    # LOD Configuration
    lod_levels: List[LODLevel] = field(default_factory=list)

    # Texture Settings
    textures: TextureSettings = field(default_factory=TextureSettings)

    # Material Configuration
    materials: Dict[str, MaterialProfile] = field(default_factory=dict)

    # Export Settings
    export_format: ExportFormat = ExportFormat.FBX
    export_settings: Dict[str, Any] = field(default_factory=dict)

    # Quality Requirements
    max_texture_memory_mb: float = 256.0
    requires_uv_unwrap: bool = True
    requires_lods: bool = True
    requires_collision_mesh: bool = False

    # Validation Criteria
    min_uv_coverage: float = 0.80
    allow_ngons: bool = False
    allow_tris: bool = True
    prefer_quads: bool = True

    # Metadata
    description: str = ""
    target_performance: str = "high"  # low, medium, high, ultra


# ==============================================================================
# PREDEFINED GAME PROFILES
# ==============================================================================

WAR_THUNDER_PROFILE = GameAssetProfile(
    name="War Thunder",
    engine=GameEngine.WAR_THUNDER,
    lod_levels=[
        LODLevel(
            name="LOD0",
            max_triangles=80000,
            reduction_ratio=1.0,
            distance_min=0,
            distance_max=50,
            description="Close-up detail (cockpit view, close combat)"
        ),
        LODLevel(
            name="LOD1",
            max_triangles=40000,
            reduction_ratio=0.5,
            distance_min=50,
            distance_max=200,
            description="Medium distance (normal combat range)"
        ),
        LODLevel(
            name="LOD2",
            max_triangles=20000,
            reduction_ratio=0.25,
            distance_min=200,
            distance_max=500,
            description="Far distance (reconnaissance, air superiority)"
        ),
        LODLevel(
            name="LOD3",
            max_triangles=10000,
            reduction_ratio=0.125,
            distance_min=500,
            distance_max=2000,
            description="Very far distance (strategic map view)"
        ),
    ],
    textures=TextureSettings(
        albedo_size=4096,
        normal_size=4096,
        roughness_size=2048,
        metallic_size=2048,
        ao_size=2048,
        format="PNG",
        compression=True
    ),
    materials=NAVAL_MATERIALS,
    export_format=ExportFormat.FBX,
    export_settings={
        "apply_modifiers": True,
        "use_mesh_modifiers": True,
        "use_armature_deform_only": False,
        "bake_anim": False,
        "path_mode": "COPY",
        "embed_textures": True,
        "axis_forward": "-Z",
        "axis_up": "Y",
        "global_scale": 1.0,
    },
    max_texture_memory_mb=512.0,
    requires_collision_mesh=True,
    target_performance="high",
    description="War Thunder naval vessel profile (Gaijin Entertainment)"
)


WORLD_OF_WARSHIPS_PROFILE = GameAssetProfile(
    name="World of Warships",
    engine=GameEngine.WORLD_OF_WARSHIPS,
    lod_levels=[
        LODLevel(
            name="LOD0",
            max_triangles=50000,
            reduction_ratio=1.0,
            distance_min=0,
            distance_max=100,
            description="Close-up detail (port view, close quarters)"
        ),
        LODLevel(
            name="LOD1",
            max_triangles=25000,
            reduction_ratio=0.5,
            distance_min=100,
            distance_max=300,
            description="Medium distance (engagement range)"
        ),
        LODLevel(
            name="LOD2",
            max_triangles=12000,
            reduction_ratio=0.24,
            distance_min=300,
            distance_max=800,
            description="Far distance (long-range artillery)"
        ),
        LODLevel(
            name="LOD3",
            max_triangles=6000,
            reduction_ratio=0.12,
            distance_min=800,
            distance_max=2000,
            description="Maximum render distance"
        ),
    ],
    textures=TextureSettings(
        albedo_size=4096,
        normal_size=4096,
        roughness_size=2048,
        metallic_size=2048,
        ao_size=2048,
        format="PNG",
        compression=True
    ),
    materials=NAVAL_MATERIALS,
    export_format=ExportFormat.FBX,
    export_settings={
        "apply_modifiers": True,
        "use_mesh_modifiers": True,
        "bake_anim": False,
        "path_mode": "COPY",
        "embed_textures": True,
        "axis_forward": "-Z",
        "axis_up": "Y",
    },
    max_texture_memory_mb=384.0,
    requires_collision_mesh=True,
    target_performance="high",
    description="World of Warships profile (Wargaming.net)"
)


UNITY_ASSET_STORE_PROFILE = GameAssetProfile(
    name="Unity Asset Store",
    engine=GameEngine.UNITY,
    lod_levels=[
        LODLevel(
            name="LOD0",
            max_triangles=50000,
            reduction_ratio=1.0,
            distance_min=0,
            distance_max=100,
            description="High detail"
        ),
        LODLevel(
            name="LOD1",
            max_triangles=25000,
            reduction_ratio=0.5,
            distance_min=100,
            distance_max=250,
            description="Medium detail"
        ),
        LODLevel(
            name="LOD2",
            max_triangles=12000,
            reduction_ratio=0.24,
            distance_min=250,
            distance_max=500,
            description="Low detail"
        ),
        LODLevel(
            name="LOD3",
            max_triangles=6000,
            reduction_ratio=0.12,
            distance_min=500,
            distance_max=1000,
            description="Culling LOD"
        ),
    ],
    textures=TextureSettings(
        albedo_size=4096,
        normal_size=4096,
        roughness_size=2048,
        metallic_size=2048,
        ao_size=2048,
        format="PNG",
        compression=False  # Let Unity handle compression
    ),
    materials=NAVAL_MATERIALS,
    export_format=ExportFormat.FBX,
    export_settings={
        "apply_modifiers": True,
        "use_mesh_modifiers": True,
        "bake_anim": False,
        "path_mode": "COPY",
        "embed_textures": False,  # Unity prefers separate textures
        "axis_forward": "-Z",
        "axis_up": "Y",
        "apply_scale_options": "FBX_SCALE_ALL",
    },
    max_texture_memory_mb=256.0,
    target_performance="medium",
    description="Unity Asset Store general-purpose profile"
)


UNREAL_ENGINE_PROFILE = GameAssetProfile(
    name="Unreal Engine",
    engine=GameEngine.UNREAL,
    lod_levels=[
        LODLevel(
            name="LOD0",
            max_triangles=80000,
            reduction_ratio=1.0,
            distance_min=0,
            distance_max=100,
            description="Nanite detail (UE5+)"
        ),
        LODLevel(
            name="LOD1",
            max_triangles=40000,
            reduction_ratio=0.5,
            distance_min=100,
            distance_max=300,
            description="High detail"
        ),
        LODLevel(
            name="LOD2",
            max_triangles=20000,
            reduction_ratio=0.25,
            distance_min=300,
            distance_max=700,
            description="Medium detail"
        ),
        LODLevel(
            name="LOD3",
            max_triangles=10000,
            reduction_ratio=0.125,
            distance_min=700,
            distance_max=1500,
            description="Low detail"
        ),
    ],
    textures=TextureSettings(
        albedo_size=4096,
        normal_size=4096,
        roughness_size=4096,
        metallic_size=4096,
        ao_size=4096,
        format="TGA",  # Unreal prefers TGA
        compression=False
    ),
    materials=NAVAL_MATERIALS,
    export_format=ExportFormat.FBX,
    export_settings={
        "apply_modifiers": True,
        "use_mesh_modifiers": True,
        "bake_anim": False,
        "path_mode": "COPY",
        "embed_textures": False,
        "axis_forward": "X",  # Unreal uses X-forward
        "axis_up": "Z",
        "apply_scale_options": "FBX_SCALE_ALL",
    },
    max_texture_memory_mb=512.0,
    requires_collision_mesh=True,
    target_performance="ultra",
    description="Unreal Engine 5+ profile with Nanite support"
)


# ==============================================================================
# PROFILE REGISTRY
# ==============================================================================

GAME_PROFILES: Dict[str, GameAssetProfile] = {
    "war_thunder": WAR_THUNDER_PROFILE,
    "world_of_warships": WORLD_OF_WARSHIPS_PROFILE,
    "unity": UNITY_ASSET_STORE_PROFILE,
    "unreal": UNREAL_ENGINE_PROFILE,
    "asset_store": UNITY_ASSET_STORE_PROFILE,  # Alias
}


def get_profile(profile_name: str) -> GameAssetProfile:
    """Get a game asset profile by name"""
    profile_name = profile_name.lower().replace(" ", "_").replace("-", "_")

    if profile_name not in GAME_PROFILES:
        raise ValueError(
            f"Unknown profile: {profile_name}. "
            f"Available profiles: {', '.join(GAME_PROFILES.keys())}"
        )

    return GAME_PROFILES[profile_name]


def list_profiles() -> List[str]:
    """List all available profile names"""
    return list(GAME_PROFILES.keys())


def create_custom_profile(
    name: str,
    lod0_triangles: int = 50000,
    lod_count: int = 4,
    texture_size: int = 4096,
    export_format: ExportFormat = ExportFormat.FBX
) -> GameAssetProfile:
    """Create a custom profile with simplified parameters"""

    # Generate LOD levels with automatic reduction
    lod_levels = []
    for i in range(lod_count):
        reduction = 0.5 ** i
        lod_levels.append(
            LODLevel(
                name=f"LOD{i}",
                max_triangles=int(lod0_triangles * reduction),
                reduction_ratio=reduction,
                distance_min=i * 100,
                distance_max=(i + 1) * 250,
                description=f"LOD level {i}"
            )
        )

    return GameAssetProfile(
        name=name,
        engine=GameEngine.CUSTOM,
        lod_levels=lod_levels,
        textures=TextureSettings(
            albedo_size=texture_size,
            normal_size=texture_size,
            roughness_size=texture_size // 2,
            metallic_size=texture_size // 2,
            ao_size=texture_size // 2,
        ),
        materials=NAVAL_MATERIALS,
        export_format=export_format,
        description=f"Custom profile: {name}"
    )


# ==============================================================================
# VALIDATION UTILITIES
# ==============================================================================

def validate_profile(profile: GameAssetProfile) -> List[str]:
    """Validate a game asset profile configuration"""
    issues = []

    # Check LOD progression
    if profile.lod_levels:
        prev_tris = float('inf')
        for lod in profile.lod_levels:
            if lod.max_triangles > prev_tris:
                issues.append(
                    f"{lod.name} has more triangles ({lod.max_triangles}) "
                    f"than previous LOD ({prev_tris})"
                )
            prev_tris = lod.max_triangles

    # Check texture sizes are power of 2
    for attr in ['albedo_size', 'normal_size', 'roughness_size', 'metallic_size', 'ao_size']:
        size = getattr(profile.textures, attr)
        if size & (size - 1) != 0:
            issues.append(f"Texture {attr} ({size}) is not a power of 2")

    # Check materials exist
    if not profile.materials:
        issues.append("No materials defined in profile")

    return issues


if __name__ == "__main__":
    # Test profile loading
    print("Available Game Asset Profiles:")
    print("=" * 60)

    for profile_name in list_profiles():
        profile = get_profile(profile_name)
        print(f"\n{profile.name} ({profile.engine.value})")
        print(f"  LOD Levels: {len(profile.lod_levels)}")
        print(f"  LOD0 Triangles: {profile.lod_levels[0].max_triangles:,}")
        print(f"  Texture Size: {profile.textures.albedo_size}px")
        print(f"  Export Format: {profile.export_format.value.upper()}")
        print(f"  Target Performance: {profile.target_performance}")

        # Validate
        issues = validate_profile(profile)
        if issues:
            print(f"  ⚠ Validation Issues: {len(issues)}")
            for issue in issues:
                print(f"    - {issue}")
        else:
            print(f"  ✓ Profile validated")
