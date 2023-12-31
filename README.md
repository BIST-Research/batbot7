# Git Flow
Main branch is not to be used for the time being.

bench: Benchtop testing for new features. ALL new commits must atleast start at this branch before going to vehicle
vehicle: Working branch, i.e., users can rely on this branch for working code. Requires a pull request to push, and new features must be tested on bench before they can be pushed here. 

dev branches --> bench --> vehicle (protected)
