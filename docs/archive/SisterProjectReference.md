Purpose
This document summarizes the NavalForge 3D pipeline and clarifies requirements for Stage 4 (Generation & AI refinement). It is written for developers building external tooling to refine procedurally generated ship meshes.

Scope
Focuses on the Generation stage's expected inputs/outputs, the planned AI refinement interface, and the correction output schema required to close the refinement loop.

### Project Overview

**NavalForge 3D** is a hybrid programmatic-AI pipeline designed to transform 2D naval blueprint images (top and side views) into geometrically plausible 3D ship models. The system prioritizes deterministic, traceable geometry generation first, using AI only for grounding, segmentation assistance, and final refinement.

### Core Architecture: The 4-Stage Pipeline

The system is structured as four independent stages, each defined by strict input/output contracts. Implementations within stages are swappable (e.g., changing from column scanning to computer vision) as long as the contract is met.

* **Stage 1: Ingestion** (Asset Management)
* **Status:** Defined.
* **Function:** Ingests raw images, uses LLM vision to analyze and auto-crop views, applies a hierarchical tagging taxonomy, and stores assets in a PostgreSQL database with full provenance tracking.


* **Stage 2: Grounding** (Enrichment)
* **Status:** Specification.
* **Function:** Identifies the ship class and enriches the data with real-world specifications (Length/Beam/Draft) from a reference database or Google Search.
* **Output:** Validated `GroundingOutput` containing physical dimensions and geometry hints (turret positions, superstructure extent).


* **Stage 3: Extraction** (Geometry)
* **Status:** Specification (Prototype exists).
* **Function:** Transforms raster images into normalized mathematical data.
* **Outputs:**
1. **Profile Curves:** 1D normalized arrays (0.0–1.0) representing the hull's width (beam) and height/sheer distribution.
2. **Z-Level Regions (Experimental):** A color-coded map where specific colors correspond to specific deck heights (e.g., Red = Level 0, Yellow = Level 1). This bridges 2D to 3D before mesh generation.




* **Stage 4: Generation** (The Forge)
* **Status:** Specification (Not Implemented).
* **Function:** Synthesizes the 3D geometry using the outputs from Stage 2 and 3.
* **Current Approach:** "Procedural Lofting & Extrusion." It lofts the hull mesh based on profile curves and extrudes deck polygons based on Z-Level regions.



### Stage 4 Detail: Generation & Refinement

This is the integration point for the external tooling. Stage 4 is divided into procedural generation and AI refinement.

#### 1. The Procedural Base (Stage 4A & 4B)

Before refinement occurs, the system generates a "base mesh" procedurally.

* **Inputs:** Profile curves (Stage 3), Z-levels (Stage 3), and Real-world Dimensions (Stage 2).
* **Process:**
* **Hull:** Lofts cross-section curves (ellipses or naval sections) scaled by the Top/Side profiles along the Z-axis.
* **Superstructure:** Extrudes "Z-level region" polygons to specified heights and stacks them.
* **Components:** Places generic placeholder meshes (cylinders/boxes) for turrets based on "Geometry Hints."


* **Output:** A mathematically "watertight" Wavefront OBJ file.

#### 2. AI Refinement (Stage 4.4) - **Future Planned Status**

This is the specific component relevant to the external repo. It is currently in **Specification status (Not Implemented)**.

**Purpose:** The base procedural mesh lacks realistic hull curvature (true cross-sections) and fine details. The refinement stage uses an AI model (specifically referencing Gemini 3 Pro / "Nano Banana Pro") to bridge this gap.

**Planned Interface Contract**
The external tooling must accept a `RefinementInput` object:

```typescript
interface RefinementInput {
  baseMesh: string;              // The OBJ string from the procedural step
  blueprints: {
    topView: string;             // Base64 image from Stage 1
    sideView: string;            // Base64 image from Stage 1
  };
  grounding: GroundingOutput;    // Dimensions & Class info from Stage 2
  mode: 'visualization' | 'correction';
}

```

**Planned Modes:**

1. **Visualization Mode:** Generates photorealistic renders of the mesh from specific angles (Bow Quarter, Plan, Profile, etc.) to validate the mesh visually against the blueprints.
2. **Correction Mode:** Analyzes the 3D model renders against the original blueprints to identify geometric discrepancies. It returns a structured JSON of suggested corrections (e.g., "Hull too round", "Bow angle too blunt").

**Targeted Correction Output Schema:**
The tool is expected to output corrections in this format:

```json
{
  "corrections": [
    {
      "type": "hull_shape",
      "description": "Hull cross-section is too boxy amidships",
      "parameter": "hullShape",
      "currentValue": 0.5,
      "suggestedValue": 0.8,
      "magnitude": "moderate"
    }
  ],
  "confidence": 0.95,
  "reasoning": "Comparison with blueprint shows sharper chine line."
}

```

### Future Architecture Plans

* **Z-Level Encoding:** The project is moving toward "Z-Level Encoding" where height information is embedded directly into the 2D top-view images using color. The refinement tool should anticipate inputs that may include these color-coded regions.
* **Component Placement:** Future iterations will move from generic cylinders to retrieving specific turret meshes based on the identified ship class.
* **Feedback Loop:** The "Correction Mode" is intended to feed parameters back into the procedural generator (Stage 4A) to regenerate a better base mesh, creating a closed-loop refinement cycle.