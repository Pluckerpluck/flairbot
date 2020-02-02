from pathlib import Path
import logging

from csscompressor import compress
from PIL import Image

from flairbot import config

FLAIR_DIR = "./flairs"
OLD_REDDIT_SUB_DIR = "old-reddit"
NEW_REDDIT_SUB_DIR = "new-reddit"

BASE_CSS = """
    a[href^="#/"] {
        background:url(%%spritesheet%%);
        display: inline-block;
        position: relative;
        top: 4px;
        cursor:default;
    }

    .flair{
        border:none;
        padding:0px;
        background:url(%%spritesheet%%) no-repeat -9999px 0px;
        display:inline-block;
        white-space:nowrap;
        text-indent:-9999px;
        line-height:3em;
        box-sizing: border-box;
    }

    .flair:hover{
        text-indent:0;
        cursor:default;
        color:#000;
        background:#f5f5f5;
        border:0.1em solid #ddd;
        padding: 0 3px;
        border-radius:2px;
        margin:0px 3px 0px 0;
        line-height:2.8em;
    }

    span.flair:empty:before {
        color: #f5f5f5;
        content: ".";
    }
"""

logger = logging.getLogger(__name__)


#   ##     ## ######## #### ##       #### ######## #### ########  ######
#   ##     ##    ##     ##  ##        ##     ##     ##  ##       ##    ##
#   ##     ##    ##     ##  ##        ##     ##     ##  ##       ##
#   ##     ##    ##     ##  ##        ##     ##     ##  ######    ######
#   ##     ##    ##     ##  ##        ##     ##     ##  ##             ##
#   ##     ##    ##     ##  ##        ##     ##     ##  ##       ##    ##
#    #######     ##    #### ######## ####    ##    #### ########  ######


def load_image(path: Path):
    """Loads the provided image, performing some simple processing.

    This function will:
        * Trim transparent whitespace

    Parameteters
    ------------
    path: Path
        The path of the image file to load

    Returns
    -------
    Image
        The processed image
    """
    try:
        with Image.open(path) as image:
            # Convert to RGBa to remove color from transparent pixels
            image = image.convert("RGBa")
            bbox = image.getbbox()
            cropped_image = image.crop(bbox)
            return cropped_image
    except:
        logger.info("%s is an invalid image" % str(path))


def resize_image(image: Image, target_height: int, *, resample=Image.LANCZOS):
    """Resize an image proportionally to the target height."""
    adjustment = target_height / image.height
    target_width = round(image.width * adjustment)

    target_size = (target_width, target_height)
    return image.resize(target_size, resample=resample)


#   ######## ##          ###    #### ########   ######
#   ##       ##         ## ##    ##  ##     ## ##    ##
#   ##       ##        ##   ##   ##  ##     ## ##
#   ######   ##       ##     ##  ##  ########   ######
#   ##       ##       #########  ##  ##   ##         ##
#   ##       ##       ##     ##  ##  ##    ##  ##    ##
#   ##       ######## ##     ## #### ##     ##  ######


class Flair:
    """A class used to load and process reddit flairs.

    This class facilities loading both new and old reddit flairs.
    It will process the flair and provide functionality to manipulate
    the flair as required by reddit.

    Attributes
    ----------
    DEFAULT_HEIGHT: int
        The default height for old reddit flairs.
        Used if no config is given for a specific flair.
    """

    DEFAULT_HEIGHT = 30

    def __init__(self, name):
        # Initialize required variables for future methods
        self.name = name

        # Start loading images
        self.old_reddit_image = self.load_old_reddit_image()
        self.new_reddit_image = self.load_new_reddit_image()

    def load_old_reddit_image(self):
        """Loads in and processes old reddit flairs."""
        # Grab the old-reddit flairs directory
        flair_dir = Path(FLAIR_DIR).joinpath(OLD_REDDIT_SUB_DIR)
        if not flair_dir.exists():
            raise FileNotFoundError("No input directory for old reddit flairs")

        # TODO: Consider supporting more than just PNGs (but probably don't)
        target_image = flair_dir.joinpath(f"{self.name}.png")

        # If we don't have an old-reddit image, just skip it
        if not target_image.exists():
            logger.info("No old-reddit flair found for %s" % self.name)
            return None

        # Finally load and process the image
        image = load_image(target_image)

        # Check for overrides on the height
        overrides = config.get_overrides(self.name)
        target_height = overrides.get("height", Flair.DEFAULT_HEIGHT)

        return resize_image(image, target_height=target_height)

    def load_new_reddit_image(self):
        """Loads in and processes new reddit flairs."""
        # Grab the old-reddit flairs directory
        flair_dir = Path(FLAIR_DIR).joinpath(NEW_REDDIT_SUB_DIR)
        if not flair_dir.exists():
            raise FileNotFoundError("No input directory for new reddit flairs")

        # TODO: Consider supporting more than just PNGs (but probably don't)
        target_image = flair_dir.joinpath(f"{self.name}.png")

        # If we don't have an old-reddit image, just skip it
        if not target_image.exists():
            logger.info("No new-reddit flair found for %s" % self.name)
            return None

        # Finally load and process the image
        return load_image(target_image)


class ComboFlair:
    def __init__(self, name, flairs):
        self.name = name

        logger.info(
            "Building combo flair: %s - %s" % (self.name, [x.name for x in flairs])
        )

        self._components = flairs

        # Validate all component flairs exists
        if any(x.old_reddit_image is None for x in self._components):
            raise RuntimeError("Missing one of: %s" % str(self._components))

        self.old_reddit_image = self.generate_old_reddit_image()
        self.new_reddit_image = None

    def generate_old_reddit_image(self):
        images = [x.old_reddit_image for x in self._components]

        PADDING = 1

        # Add 1 pixel padding
        width = sum(image.width + PADDING for image in images) - PADDING
        height = max(image.height for image in images)

        combo_flair = Image.new("RGBA", (int(width), int(height)))

        x_pos = 0
        for image in images:
            combo_flair.paste(image, (x_pos, 0))

            # Increment for the next image
            x_pos += image.width + PADDING

        return combo_flair


class Spritesheet:
    """A class to facilitate the generation a spritesheets of flairs.

    This class aims to provide the functionality required to create
    reddit compatible spritesheets out of a collection of flairs.

    Attributes
    ----------
    PADDING: int
        The padding to place between sprites in the spritesheet
    """

    PADDING = 3

    def __init__(self):
        self.flairs = []

    def add_flair(self, flair: Flair):
        """Add a flair to the spritesheet."""
        self.flairs.append(flair)

    def build(self):
        """Build the spritesheet.

        Builds a single row spritesheet.
        This minimizes the lines of CSS required to get the flairs
        working (and is easy to build).
        """
        old_flairs = [x for x in self.flairs if x.old_reddit_image is not None]

        # We are using padding to avoid browser interpolation issues
        total_width = sum(
            flair.old_reddit_image.width + Spritesheet.PADDING
            for flair in old_flairs
            if flair is not None
        )

        # We overcount the padding on the last image, so remove that
        total_width -= Spritesheet.PADDING

        height = max(
            flair.old_reddit_image.height for flair in old_flairs if flair is not None
        )

        # Create the blank spritesheet to add the images to
        spritesheet = Image.new("RGBA", (int(total_width), int(height)))

        # Start places the sprites into the spritesheet
        origins = {}
        x_pos = 0
        for flair in old_flairs:
            image = flair.old_reddit_image
            spritesheet.paste(image, (x_pos, 0))

            # Save the location, needed for CSS generation
            origins[flair.name] = x_pos

            # Increment for the next image
            x_pos += image.width + Spritesheet.PADDING

        # Spritesheet is now done, lets generate the CSS
        declarations = [BASE_CSS]
        for flair in old_flairs:
            # Lookup their position in the spritesheet
            x_pos = origins[flair.name]

            element = [
                f".flair-{name}, a[href='#/{name}'] {{",
                f"min-width: {flair.old_reddit_image.width}px;",
                f"height: {flair.old_reddit_image.height}px;",
                f"background-position-x: -{x_pos}px;",
                "}",
            ]

            # Add the element to the declarations
            declarations.extend(element)

        css = compress("\n".join(declarations))

        return spritesheet, css


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    # Find all flair names from png files, ignore duplicate names
    files = Path(FLAIR_DIR).glob(("**/*.png"))
    flair_names = set(file.name[:-4] for file in files if file.is_file())

    flairs = {}
    # Build up the single image flairs (order is maintained for >= 3.7)
    for name in flair_names:
        flairs[name] = Flair(name)

    for name, components in config.get_combo_flairs().items():
        sub_flairs = [flairs[x] for x in components]
        flairs[name] = ComboFlair(name, sub_flairs)

    # Generate a sorted list for stable output
    all_flairs = list(flairs.values())
    all_flairs.sort(key=lambda x: x.name)

    # Create the spritesheet
    spritesheet = Spritesheet()
    for flair in all_flairs:
        spritesheet.add_flair(flair)

    output, css = spritesheet.build()

    # Output to dist folder
    Path("dist").mkdir(exist_ok=True)
    output.save("dist/spritesheet.png")
    with open("dist/spritesheet.css", "w") as f:
        f.write(css)
