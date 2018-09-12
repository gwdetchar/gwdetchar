/*
 * Copyright (C) Alexander Urban (2018)
 *
 * This file is part of GWDetChar
 *
 * GWDetChar is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * GWDetChar is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with GWDetChar.  If not, see <http://www.gnu.org/licenses/>
 */

$(document).ready(function() {
  $(".fancybox").fancybox({
    nextEffect: 'none',
    prevEffect: 'none',
    helpers: {title: {type: 'inside'}}
  });
});

function showImage(channelName, tRanges, imageType, captions) {
  for (var tIndex in tRanges) {
    var idBase = channelName + "_" + tRanges[tIndex];
    var fileBase = channelName + "-" + imageType + "-" + tRanges[tIndex];
    document.getElementById("a_" + idBase).href =
      "plots/" + fileBase + ".png";
    document.getElementById("a_" + idBase).title = captions[tIndex];
    document.getElementById("img_" + idBase).src =
      "plots/" + fileBase + ".png";
    document.getElementById("img_" + idBase).alt = fileBase + ".png";
  };
};
