# Test Fixtures

This directory contains test fixtures for the Blender Project Manager test suite.

## Directory Structure

- `simple.blend` - Minimal .blend file with one object
- `with_textures.blend` - .blend file with image references
- `with_links.blend` - .blend file with library links
- `textures/` - Sample texture files
- `project/` - Sample project directory structure

## Creating Fixtures

Fixtures should be minimal and focused on specific test scenarios.

To create a new .blend fixture:
1. Open Blender
2. Create the minimal setup needed
3. Save to this directory
4. Document what it contains above

## Using Fixtures

Fixtures are automatically copied to temporary directories for each test,
so tests can modify them without affecting other tests.
