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

// expand fancybox plots
$(document).ready(function() {
  $(".fancybox").fancybox({
    nextEffect: 'none',
    prevEffect: 'none',
    helpers: {title: {type: 'inside'}}
  });
});

// expose alternative image types
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

// download a CSV table
function downloadCSV(csv, filename) {
  var csvFile;
  var downloadLink;
  // set download attributes
  csvFile = new Blob([csv], {type: "text/csv"});
  downloadLink = document.createElement("a");
  downloadLink.download = filename;
  downloadLink.href = window.URL.createObjectURL(csvFile);
  downloadLink.style.display = "none";
  document.body.appendChild(downloadLink);
  // download action
  downloadLink.click();
}

// export a table to CSV
function exportTableToCSV(filename, tableId) {
  var csv = [];
  var table = document.getElementById(tableId);
  var rows = table.querySelectorAll("table tr");
  // get table rows
  for (var i = 0; i < rows.length; i++) {
    var row = [], cols = rows[i].querySelectorAll("td, th");
    for (var j = 0; j < cols.length; j++)
        row.push(cols[j].innerText);
    csv.push(row.join(","));
  }
  // download CSV record
  downloadCSV(csv.join("\n"), filename);
}
