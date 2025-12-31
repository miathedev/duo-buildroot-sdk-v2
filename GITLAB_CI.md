# GitLab CI Pipeline Documentation

## Overview

This repository includes a GitLab CI/CD pipeline configuration (`.gitlab-ci.yml`) that automatically builds the MilkV Duo S MIDI adapter SD card image.

## Pipeline Stages

### 1. Build Stage

**Job: `build:duos-midi-adapter`**
- Builds the complete SD card image with MIDI adapter configuration
- Target: `milkv-duos-glibc-arm64-sd`
- Timeout: 3 hours
- Artifacts: Compressed images (`.img.zst`, `.zip.zst`)
- Retention: 30 days

**Job: `build:check-mr` (Merge Requests Only)**
- Quick validation for merge requests
- Verifies build configuration
- Validates MIDI adapter Python files
- Timeout: 30 minutes

**Job: `build:nightly` (Scheduled Only)**
- Automated nightly builds
- Same as main build job
- Artifacts retention: 7 days

### 2. Package Stage

**Job: `package:midi-adapter-release`**
- Creates release package with documentation
- Includes:
  - Compressed SD card images
  - Complete documentation (MIDI_ADAPTER.md, README.md)
  - Configuration examples
  - Quick start guide
- Creates tarball for easy distribution
- Retention: 90 days

## Build Requirements

### GitLab Runner Configuration

**Recommended Runner Specs:**
- **CPU**: 4+ cores
- **RAM**: 8GB minimum, 16GB recommended
- **Disk**: 50GB+ free space
- **Tags**: `docker`
- **Executor**: `docker`

### Docker Image

Uses `ubuntu:22.04` with the following dependencies:
- Build essentials (gcc, make, cmake, etc.)
- Buildroot dependencies
- Python 3 with required modules
- Device tree compiler
- Compression tools (zstd)

## Usage

### Automatic Builds

The pipeline automatically triggers on:
- **Push to any branch**: Full build
- **Tags**: Full build + release
- **Merge requests**: Quick validation only
- **Scheduled pipelines**: Nightly builds

### Manual Trigger

To manually trigger a build in GitLab:

1. Navigate to **CI/CD > Pipelines**
2. Click **Run pipeline**
3. Select branch
4. Click **Run pipeline**

### Download Artifacts

After a successful build:

1. Go to **CI/CD > Pipelines**
2. Click on the pipeline
3. Click on the job (e.g., `build:duos-midi-adapter`)
4. Click **Download artifacts** button

Or use GitLab CLI:

```bash
# Download build artifacts
glab ci artifact download <job-id>

# List jobs
glab ci list
```

## Artifacts

### Build Artifacts

Located in `out/` directory:
- `milkv-duos-glibc-arm64-sd_*.img.zst` - Compressed SD card image

### Release Package

Located in root directory:
- `milkv-duos-midi-adapter-<commit>.tar.gz` - Complete release package

Contains:
```
release/
├── *.img.zst                          # Compressed SD image
├── MIDI_ADAPTER.md                     # Complete documentation
├── README.md                           # Project overview
├── README.txt                          # Release notes
└── midi-adapter-config-examples/       # Configuration examples
    ├── config.json                     # Default config
    ├── examples/                       # Additional examples
    ├── README.md                       # Config documentation
    └── *.sh                            # Utility scripts
```

## Customization

### Change Build Target

Edit `.gitlab-ci.yml`:

```yaml
variables:
  TARGET_BOARD: "milkv-duos-glibc-arm64-sd"  # Change to desired target
```

Available targets:
- `milkv-duos-glibc-arm64-sd` (default, recommended for MIDI adapter)
- `milkv-duos-glibc-arm64-emmc`
- `milkv-duos-musl-riscv64-sd`
- `milkv-duos-musl-riscv64-emmc`

### Adjust Timeout

For slower runners:

```yaml
build:duos-midi-adapter:
  timeout: 4h  # Increase from 3h
```

### Change Artifact Retention

```yaml
artifacts:
  expire_in: 60 days  # Change from 30 days
```

### Add Additional Builds

Create a new job:

```yaml
build:duos-midi-emmc:
  extends: .build_template
  stage: build
  variables:
    TARGET_BOARD: "milkv-duos-glibc-arm64-emmc"
  script:
    - ./build.sh ${TARGET_BOARD}
    # ... rest of build steps
```

## Scheduled Pipelines

### Setup Nightly Builds

In GitLab:

1. Go to **CI/CD > Schedules**
2. Click **New schedule**
3. Configure:
   - **Description**: "Nightly MIDI Adapter Build"
   - **Interval pattern**: `0 2 * * *` (2 AM daily)
   - **Target branch**: `main`
   - **Active**: ✓
4. Click **Save pipeline schedule**

The `build:nightly` job will run automatically.

## Troubleshooting

### Build Fails: Out of Disk Space

Increase runner disk space or add cleanup:

```yaml
before_script:
  - df -h
  - apt-get clean
  - rm -rf /var/lib/apt/lists/*
```

### Build Fails: Missing Dependencies

Add missing packages to `before_script`:

```yaml
before_script:
  - apt-get install -y <missing-package>
```

### Timeout Issues

Increase job timeout or use faster runner:

```yaml
timeout: 4h
```

### Python Validation Fails

Check Python syntax:

```bash
python3 -m py_compile device/generic/rootfs_overlay/duos/root/midi-adapter/midi_adapter.py
```

## CI/CD Variables

You can set these in GitLab UI (**Settings > CI/CD > Variables**):

| Variable | Description | Default |
|----------|-------------|---------|
| `TARGET_BOARD` | Build target | `milkv-duos-glibc-arm64-sd` |
| `ARCH` | Architecture | `riscv` |
| `GIT_DEPTH` | Clone depth | `1` |

## Performance Tips

### Speed Up Builds

1. **Use cache** for buildroot downloads:
   ```yaml
   cache:
     key: buildroot-dl
     paths:
       - buildroot/dl/
   ```

2. **Use faster runner** with more CPU cores

3. **Enable ccache**:
   ```yaml
   cache:
     key: ccache
     paths:
       - .ccache/
   ```

### Reduce Artifact Size

Images are automatically compressed with `zstd` for faster upload/download.

To decompress:
```bash
zstd -d milkv-duos-*.img.zst
```

## Integration with Git

### Protect Main Branch

Require successful pipeline before merge:

1. **Settings > Repository > Protected branches**
2. Select `main` branch
3. Enable: **Allowed to push**: No one
4. Enable: **Allowed to merge**: Maintainers
5. Check: **Pipelines must succeed**

### Merge Request Workflow

1. Create branch
2. Make changes
3. Push branch → triggers `build:check-mr` (quick validation)
4. Create merge request
5. Wait for validation
6. If approved, merge → triggers full build

## Support

For issues with the CI pipeline:
1. Check GitLab CI/CD logs
2. Review this documentation
3. Open an issue in the repository

For MIDI adapter specific issues, see [MIDI_ADAPTER.md](MIDI_ADAPTER.md).
