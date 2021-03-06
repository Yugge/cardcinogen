import unittest

import sys
import os
import json
import textwrap
from util import sysfont, util
from PIL import Image, ImageDraw, ImageFont


class TextLabel:
  """ Parsed version of a single text-label object """

  def __init__(self, json):
    """ Parse out the various settings of a text label and clean them up """
    self.source =   util.get_default(json, "source", "text.txt")
    self.type =     util.get_default(json, "type", "simple")
    self.x =        util.get_default(json, "x", 10, int)
    self.y =        util.get_default(json, "y", 10, int)
    self.width =    util.get_default(json, "width", 40000, int)
    self.height =   util.get_default(json, "height", 40000, int)
    self.color =    util.get_default(json, "color", "#000000")
    self.fontface = util.get_default(json, "font-face", "sans")
    self.fontsize = util.get_default(json, "font-size", 12, int)
    self.spacing  = util.get_default(json, "line-spacing", 4, int)
    weight =        util.get_default(json, "font-weight", "regular")

    self.fontweight = sysfont.STYLE_NORMAL
    if (weight == "bold"):   self.fontweight = sysfont.STYLE_BOLD
    if (weight == "italic"): self.fontweight = sysfont.STYLE_ITALIC

    # Try to auto-select a font based on the user's string
    candidate_font = sysfont.get_font(self.fontface, self.fontweight)
    if (candidate_font is None):
      # Fallback to arial
      sys.stderr.write("Unable to locate font %s. Falling back to Arial.\n" % self.fontface)
      candidate_font = sysfont.get_font("arial black", self.fontweight)

    self.font = ImageFont.load_default()
    if (candidate_font is not None):
      self.font = ImageFont.truetype(candidate_font, self.fontsize)

  def wrap_pixel_width(self, text, maxwidth):
    """ Split into a list of text lines, such that none of them exceeds the pixel width """
    ret = []

    # Start by respecting any \n newlines in the text
    paragraphs = text.split('\\n')

    # Each of those sections is wrapped individually
    for paragraph in paragraphs:
      for chars in range(len(paragraph), 1, -1):
        lines = textwrap.wrap(paragraph, chars)
        too_wide = False
        for l in lines:
          lw, _ = self.font.getsize(l)
          if (lw > maxwidth): too_wide = True

        if (not too_wide):
          ret += lines
          break

    if (len(ret) == 0): ret = None
    return ret

  def render(self, dimensions, text):
    """ Generate a transparent PIL card layer with the text on it """
    # If the user has set a max width, respect that.
    # If not, we use the edge of the card.
    # Ditto for the height
    maxwidth = min(dimensions[0] - self.x, self.width)
    maxheight = min(dimensions[1] - self.y, self.height)

    # Split the text into lines, in a way that fits our width
    lines = self.wrap_pixel_width(text, maxwidth)

    if (lines is None):
      sys.stderr.write("Warning: Unable to wrap text label \"%s\"\n" % text)
      return None

    image = Image.new("RGBA", dimensions, (0,0,0,0))
    draw = ImageDraw.Draw(image)

    # Render the text, one line at a time
    y = self.y
    for l in lines:
      w,h = self.font.getsize(l)
      draw.text((self.x, y), l, font=self.font, fill=self.color)
      y += h + self.spacing

    if ((y - self.y) > maxheight):
      sys.stderr.write("Warning: Text label overflows max height: \"%s\"\n" % text)
      return None

    return image

class TextLabelComplex:
  """ Parsed version of a complex text-label object """

  def __init__(self, json, rootdir):
    self.source =       util.get_default(json, "source", "text.json")
    self.type =         util.get_default(json, "type", "simple")
    self.frontSource =  util.get_default(json, "front", "")
    self.subLabels =    util.get_default(json, "texts", [])
    self.directory =    rootdir


  def wrap_pixel_width(self, text, maxwidth, font):
    """ Split into a list of text lines, such that none of them exceeds the pixel width """
    ret = []

    # Start by respecting any \n newlines in the text
    paragraphs = text.split('\n')

    # Each of those sections is wrapped individually
    for paragraph in paragraphs:
      if (paragraph == ""): # respect empty lines...
        ret += [" "]
        continue

      for chars in range(len(paragraph), 1, -1):
        lines = textwrap.wrap(paragraph, chars)
        too_wide = False
        for l in lines:
          lw, _ = font.getsize(l)
          if (lw > maxwidth): too_wide = True

        if (not too_wide):
          ret += lines
          break


    if (len(ret) == 0): ret = None
    return ret

  def render(self, dimensions, texts):
    """ Generate a transparent PIL card layer with the text on it """
    # If the user has set a max width, respect that.
    # If not, we use the edge of the card.
    # Ditto for the height
    image = Image.new("RGBA", dimensions, (0,0,0,0))
    if (self.frontSource != ""):
      path = os.path.join(self.directory, self.frontSource)
      front = Image.open(path, 'r')
      image.paste(front, (0,0))

    for label in self.subLabels:

      x =        util.get_default(label, "x", 10, int)
      y =        util.get_default(label, "y", 10, int)
      width =    util.get_default(label, "width", 40000, int)
      height =   util.get_default(label, "height", 40000, int)
      color =    util.get_default(label, "color", "#000000")
      fontface = util.get_default(label, "font-face", "sans")
      fontsize = util.get_default(label, "font-size", 12, int)
      spacing  = util.get_default(label, "line-spacing", 4, int)
      weight =   util.get_default(label, "font-weight", "regular")
      rotation = util.get_default(label, "rotation", 0, int)
      wordwrap = util.get_default(label, "wordwrap", True)
      name =     util.get_default(label, "name", "")

      text =     util.get_default(texts, name, "")

      fontweight = sysfont.STYLE_NORMAL
      if (weight == "bold"):   fontweight = sysfont.STYLE_BOLD
      if (weight == "italic"): fontweight = sysfont.STYLE_ITALIC

      # Try to auto-select a font based on the user's string
      candidate_font = sysfont.get_font(fontface, fontweight)
      if (candidate_font is None):
        # Fallback to arial
        sys.stderr.write("Unable to locate font %s. Falling back to Arial.\n" % fontface)
        candidate_font = sysfont.get_font("arial black", fontweight)

      font = ImageFont.load_default()
      if (candidate_font is not None):
        font = ImageFont.truetype(candidate_font, fontsize)

      maxwidth = min(dimensions[0] - x, width)
      maxheight = min(dimensions[1] - y, height)

      # Split the text into lines, in a way that fits our width
      if (wordwrap):
        lines = self.wrap_pixel_width(text, maxwidth, font)
      else:
        lines = [text]

      if (lines is None):
        sys.stderr.write("Warning: Unable to wrap text label \"%s\"\n" % text)
        return None

      draw = ImageDraw.Draw(image)

      maxDim = max(dimensions[0], dimensions[1])
      rotationImage = Image.new("RGBA", (maxDim, maxDim))
      if (rotation != 0):
        draw = ImageDraw.Draw(rotationImage)

      # Render the text, one line at a time
      y_ = y
      for l in lines:
        w,h = font.getsize(l)
        draw.text((x, y_), l, font=font, fill=color)
        y_ += h + spacing

      if ((y_ - y) > maxheight):
        sys.stderr.write("Warning: Text label overflows max height: \"%s\"\n" % text)
        return None

      if (rotation != 0):
        rot = rotationImage.rotate(rotation)
        image.paste(rot, (0,0) , rot)


    return image


class TextGenerator:

  def __init__(self, directory):
    self.directory = directory
    self.loaded = {}


  def gen(self, filename):
    if (filename not in self.loaded):
      path = os.path.join(self.directory, filename)
      handle = open(path, "r")
      if (handle is None):
        sys.stderr.write("Unable to open text file %s\n" % path)
        return None
      self.loaded[filename] = handle

    line = self.loaded[filename].readline().rstrip()
    if (line == ""):
      # End of file
      return None
    return line

  def gen_complex(self, filename):
    if (filename not in self.loaded):
      path = os.path.join(self.directory, filename)
      handle = open(path, "r")
      if (handle is None):
        sys.stderr.write("Unable to open json file %s\n" % path)
        return None
      self.loaded[filename] = json.load(handle)

    if (len(self.loaded[filename]) == 0):
      #End of file
      return None
    texts = self.loaded[filename].pop()
    return texts

#
# Unit tests
#
class TestTextStuff(unittest.TestCase):

  def test_text_init(self):
    # This one makes use of all the default values
    lab_default = TextLabel({})
    self.assertEqual(lab_default.x, 10)
    self.assertEqual(lab_default.y, 10)
    self.assertEqual(lab_default.width, 40000)
    self.assertEqual(lab_default.height, 40000)
    self.assertEqual(lab_default.color, "#000000")
    self.assertEqual(lab_default.source, "text.txt")
    self.assertEqual(lab_default.fontface, "sans")
    self.assertEqual(lab_default.fontsize, 12)
    self.assertEqual(lab_default.spacing, 4)

    # This one overrides every possible setting
    dic = {
      "source": "phrases.txt",
      "x": 20,
      "y": 30,
      "width": 300,
      "height": 200,
      "color": "#DEADBE",
      "font-face": "courier new",
      "font-size": 32,
      "font-weight": "bold",
      "line-spacing": 12
    }

    lab_override = TextLabel(dic)

    self.assertEqual(lab_override.source, dic["source"])
    self.assertEqual(lab_override.x, dic["x"])
    self.assertEqual(lab_override.y, dic["y"])
    self.assertEqual(lab_override.width, dic["width"])
    self.assertEqual(lab_override.height, dic["height"])
    self.assertEqual(lab_override.color, dic["color"])
    self.assertEqual(lab_override.fontface, dic["font-face"])
    self.assertEqual(lab_override.fontsize, dic["font-size"])
    self.assertEqual(lab_override.spacing, dic["line-spacing"])

  def test_render_text(self):
    lab_default = TextLabel({ "color": "#AABBCC" })
    layer = lab_default.render((100, 30), "Hello")
    self.assertEqual(layer.width, 100)
    self.assertEqual(layer.height, 30)
    # There are some transparent pixels and some of the text color. Good enough.
    self.assertEqual(layer.getextrema(), ((0, 0xAA), (0, 0xBB), (0, 0xCC), (0, 255)))

  # TODO: Test text wrapping

if __name__ == '__main__':
    unittest.main()

