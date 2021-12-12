## Documentation

This component works by submitting a csv of the catalog and basket as well as a .json file of offers. Example files have been submitted in the test_data directory. The documentation doesn't say a preferred input method so I went with this for this exercise. I felt submitting csvs and jsons was an easy input method and easy to share with other applications and systems.

You can run the basket_pricer.py directly, or change the input files to experiment with its functionality.

The tests are run with pytest

The requirements file should have all the necessary libraries to run the program.

Basket 2 for the examples list the discount as .95 however, the correct amount is .945. My program rounds the penny up but the requirements dont state to round the penny down in such a situation. Anyways I could change this if that was a requirement to round fractions of a penny down.