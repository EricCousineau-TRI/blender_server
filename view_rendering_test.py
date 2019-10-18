#!/usr/bin/env python3

"""
For running, download the race spaceship blend, then set up, with matplotlib.

Doing so in Ubuntu Bionic can be seen in `setup_bionic.py`, and used via:

    setup_bionic.py --with_jupyter
"""

import os
try:
    import bpy
except ImportError:
    # Execution trampoline.
    assert __name__ == "__main__"
    binary = "blender"
    os.execvp(
        binary, [
            binary,
            # Need window for using view render.
            "--window-geometry", "100", "100", "200", "200",
            # Re-execute this file.
            "--python", __file__,
        ])

import matplotlib.pyplot as plt
import numpy as np


def setup_compositor_nodes(add_contrast):
    # https://ammous88.wordpress.com/2015/01/16/blender-access-render-results-pixels-directly-from-python-2/
    bpy.context.scene.use_nodes = True
    tree = bpy.context.scene.node_tree
    links = tree.links
    # clear default nodes
    for n in tree.nodes:
        tree.nodes.remove(n)
    # create input render layer node
    rl = tree.nodes.new('CompositorNodeRLayers')
    rl.name = "Render Layers"
    rl.layer = "All"
    img = rl.outputs["Image"]

    # Maybe create contrast.
    if add_contrast:
        bc = tree.nodes.new("CompositorNodeBrightContrast")
        bc.name = "Contrast"
        bc.inputs["Contrast"].default_value = 1.3
        links.new(rl.outputs["Image"], bc.inputs["Image"])
        img = bc.outputs["Image"]

    # create output node
    v = tree.nodes.new('CompositorNodeViewer')
    v.name = "Viewer"
    v.use_alpha = False
    # Links
    links.new(img, v.inputs["Image"])  # link Image output to Viewer input


def main():
    # https://download.blender.org/demo/eevee/race_spaceship/race_spaceship.blend
    bpy.ops.wm.open_mainfile(filepath=os.path.expanduser("~/Downloads/race_spaceship.blend"))
    # With or without contrast, still see a diff.
    setup_compositor_nodes(add_contrast=False)

    file_direct = "/tmp/test_file.png"
    bpy.context.scene.render.image_settings.file_format = "PNG"
    bpy.context.scene.render.filepath = file_direct
    bpy.ops.render.render(write_still=True)

    b_image = bpy.data.images['Viewer Node']
    w, h = b_image.size
    img_view = np.array(b_image.pixels[:]).reshape((h, w, b_image.channels))
    img_view = img_view[::-1, :, :3]
    # Why is this necesssary? Why do I get values >1?
    img_view = np.clip(img_view, 0, 1)
    file_view = "/tmp/test_view.png"
    plt.imsave(file_view, img_view)

    # Save absolut difference.
    img_direct = plt.imread(file_direct)
    img_direct = img_direct[:, :, :3]
    img_diff = np.abs(img_direct - img_view)
    file_diff = "/tmp/test_diff.png"
    plt.imsave(file_diff, img_diff)

    print(f"Saved:")
    print(f"  {file_direct}")
    print(f"  {file_view}")
    print(f"  {file_diff}")


if __name__ == "__main__":
    main()
