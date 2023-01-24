# StudyingWebsite

## To Run
1. Download the repository
2. Install Flask (This project uses version 2.2.2)
3. Run flask app called 'study'
## Functionality
- Users can create decks as a set of questions and answers
- Users can study a given deck by asking question, flashcard, multiple choice, fill in the blanks
- Users can see statistics for how how they perform on any deck or term
- Users can create and join classes, and share decks in a class
- Users can view and study public decks

# Post Mortem
## Overall
Overall this project has taught me a lot, mainly about how to do a big project like this. Testing, prototyping, modularity, comments, documentation (especially about more complex features), and timelining.
## Pros
+ The site kind of works. You can revise decks with routines and use spaced repetition
+ The spaced repetition is quite powerful and useful compared to other studying websites
+ There are a few good ways to revise
## Cons
- No testing led to having to go back and fix bugs during development
- No testing also meant when some code was changed, it sometimes broke a lot of previous code. This wasn't noticed as there was no testing of the code with each change, so broken code was randomly found during usage
- Statistics is unimpressive. No graphs or charts or date filtering, this is an area that did not come out as it should have. Graphs were included for some time but eventually were scrapped because, to be honest, I didn't totally understand what was going on. Copied code from tutorials was twisted around and it was a nightmore to maintain or add features to.
- No prototyping meant the design and scope of the project changed during development but only one codebase was ever created, leading to a messy and convoluted change that slowed me down
- The CSS is a nightmare! A lot of the CSS is repetitive font styling. Now I know more about CSS and some tips on how to use it, I won't produce CSS of such low quality in the future