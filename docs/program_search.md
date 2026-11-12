# Program and location search

The older career-card design is retained. College programs and TESDA qualifications
are plain text lists; none of those names is a link.

The existing bottom button for college or TESDA opens a native HTML dialog first,
even with a saved area. Choose any mapped program and enter a city or province.
No location lookup happens during page load or result rendering. Explicitly
choosing Use my current location requests browser permission and resolves an
approximate province locally on the backend; learners can replace it with a city.
HTTPS or localhost is required for browser geolocation. Failure leaves manual
entry available. Only the entered area is remembered in localStorage.

Search opens a new tab during the submit click:
- TESDA: https://www.tesda.gov.ph/Tvi/Result using SearchCourse and SearchLoc.
- College: Google web search search using the chosen program and city/province.

No local verified campus directory is supplied. A geographic search does not
establish course availability, admission eligibility, or an actual distance-ranked
nearest school. Confirm the chosen campus and course directly with the institution.

The work buttons retain direct searches: Jobstreet for employment, Jobstreet
for remote work, using the career title with remote as search keywords. No job or
school application is submitted by this app.
