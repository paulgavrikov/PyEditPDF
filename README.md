# PyEditPDF


### Dependencies

This app relies on `pdfrw` for the PDF logic which hasn't seen a commit in years. So, there may be bugs. 
The other big dependency is `pdf2image`, for displaying the PDF, which itself relies on `Poppler`. 
You're probably good with most Linux distros, including recent `Ubuntu` and it's variants, but if you experience any
issues regarding it try the following depending on your OS.

#### Conda (all OS, recommended):
`conda install -c conda-forge poppler`

#### Linux:

Test `pdftoppm` and `pdftocairo` commands. If one of the is missing try to install `poppler-utils` with your package
manager.

### Windows

Install `Poppler`. The libraray authors recommend 
[@oschwartz10612 version](https://github.com/oschwartz10612/poppler-windows/releases/) which is the most up-to-date. 
You will then have to add the `bin/` folder to [PATH](https://www.architectryan.com/2018/03/17/add-to-the-path-on-windows-10/).

### Mac

Install [poppler for Mac](http://macappstore.org/poppler/).