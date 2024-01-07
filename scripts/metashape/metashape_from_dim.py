import sys
from pathlib import Path

sys.path.append(Path(__file__))

import Metashape
from ms_utils import cameras_from_bundler, create_new_project, import_markers

root_dir = Path("/home/francesco/casalbagliano/subset_A")

# name = "casalbagliano_superpoint+lightglue_bruteforce"
name = "results_superpoint+lightglue_matching_lowres_quality_high"

images_dir = root_dir / "images"
project_path = root_dir / "metashape" / f"{name}.psx"
marker_image_path = root_dir / "metashape" / "subset_full_markers.txt"
marker_world_path = root_dir / "metashape" / "subset_full_markers_world.txt"

sfm_dir = root_dir / name
bundler_file_path = sfm_dir / "reconstruction" / "bundler.out"
bundler_im_list = sfm_dir / "reconstruction" / "bundler_list.txt"

prm_to_optimize = {
    "f": True,
    "cx": True,
    "cy": True,
    "k1": True,
    "k2": True,
    "k3": True,
    "k4": False,
    "p1": True,
    "p2": True,
    "b1": False,
    "b2": False,
    "tiepoint_covariance": True,
}


def main():
    image_list = list(images_dir.glob("*"))
    images = [str(x) for x in image_list if x.is_file()]

    doc = create_new_project(str(project_path), read_only=False)
    chunk = doc.chunk

    # Add photos to chunk
    chunk.addPhotos(images)
    cameras_from_bundler(
        chunk=chunk,
        fname=bundler_file_path,
        image_list=bundler_im_list,
    )

    # Import markers image coordinates
    import_markers(
        marker_image_file=marker_image_path,
        chunk=chunk,
    )

    # Import markers world coordinates
    chunk.importReference(
        path=str(marker_world_path),
        format=Metashape.ReferenceFormatCSV,
        delimiter=",",
        skip_rows=1,
        columns="noxyz",
    )

    # optimize camera alignment
    chunk.optimizeCameras(
        fit_f=prm_to_optimize["f"],
        fit_cx=prm_to_optimize["cx"],
        fit_cy=prm_to_optimize["cy"],
        fit_k1=prm_to_optimize["k1"],
        fit_k2=prm_to_optimize["k2"],
        fit_k3=prm_to_optimize["k3"],
        fit_k4=prm_to_optimize["k4"],
        fit_p1=prm_to_optimize["p1"],
        fit_p2=prm_to_optimize["p2"],
        fit_b1=prm_to_optimize["b1"],
        fit_b2=prm_to_optimize["b2"],
        tiepoint_covariance=prm_to_optimize["tiepoint_covariance"],
    )

    # save project
    doc.read_only = False
    doc.save()


if __name__ == "__main__":
    main()
