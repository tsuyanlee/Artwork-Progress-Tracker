<!-- 
At first I used ChatGPT to quickly write the Markdown file for me. 
But this is one of those times where you want to make sure your effort matters.

 -->



# Artwork Progress Tracker

This is @tsuyanlee (DaveDrafts), I created this tool to track my work, mostly the artworks that I have made so far.  
I love organising my work, so I have dedicated folders to store my work.  
This is one of those tools that I made to smoothen my work process, and many more are yet to come.  
I did use ChatGPT at first to generate a template for the tool, I didnt have much time in the begining due to various projects.  
The generated code had so many issues I had to fix it one by one later on when I had the time.  
I do regret using it in the begining of this, but on solo projects (which it was in the begining) I had to chose convenience.  
I apologise if I hurted any of your feelings. Just think of me as a developer tight on time and budget.
  
`You can use this tool to not just track artworks, but also on all types of files that you have stored.`

---
## Inspiration
GitHub style Progress Tracker that shows a calendar in which how many commits have been performed.  
A similar approach to passively track file changes in a folder.  
Without the use of GitHub.

---

## Versions

### Drafts

| Version | Details|
|-------|-----|
| V0.1 | Just Showed a calendar with no text.
| V0.2 | Added Calendar texts and a save png button to export the calendar.
| V0.3 | Worked on adding other folders from different directories
| V0.4 | Added Data visualization for the Work Done days compared to inactive(Pie Chart.)
| V0.5 | Other Graphs (Line) Daily Contributions and (Bar) for different file types.
| V0.6 | Added tracking system to track any modifications done on saved work file using trackin.json. 

### Launched
| Version | Details|
|-------|-----|
| V1.00 |  Uploaded the source code to GitHub.
| [V1.01](https://github.com/tsuyanlee/Artwork-Progress-Tracker/tree/main) | **Bug Fixes**, Fixed where the modification count was +2 when launching the app if the changes were made the next day.
| V1.10 | **Feature Fixes** Added text on the exported image of Calendar.
| V1.20 | **Feature Added** Added Export Charts that exported the Graphs and Charts into Images.
| [V1.21](https://github.com/tsuyanlee/Artwork-Progress-Tracker/tree/Save-Graph-feature) | **Bug Fixes** Fixed an invisble bug with the text of Libe Graph. 


---

## Instructions

Clone the github repo  
```bash
git clone https://github.com/tsuyanlee/Artwork-Progress-Tracker
```

1. (Optional)Add the GUY.py code to your dedicated folder, this will be the default folder that opens the same Directory.
1. Run the code.
```bash 
python GUY.py
```
3. Click on Update Charts to show data visualization in the form of vrious charts.
4. Click on Save Png to save the calendar as a png file. Give the appropriate name.
5. Hover on the days of calendar to see the number work done and modifications made on that specific day.
6. Click on the day to see the names of files that you worked on that day.
7. Click on Export Chart to export the charts as .png files.
---

## Requirements

- Python 3.9 or newer
- Standard library only
- Optional (for PNG export):
  ```bash
  pip install pillow

## License

The MIT License (MIT)
Copyright © 2025 DaveDrafts

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the “Software”), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
