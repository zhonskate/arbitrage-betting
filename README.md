# Arbitrage betting

This is a simple script to explore the idea of arbitrage betting.

## How to use it

* 1. Clone the repo.

* 2. Go to [the odds api](https://the-odds-api.com/) and get your api key. You should save it in a file in the root directory called `key.txt`. It'll look like this:

    ```
    ├── README.md
    ├── key.txt
    └── parser.py
    ```

* 3. Run `python parser.py`.

## Configuration options.

### Settings

There are some configuration options in `parser.py`:

*  **verbosity**: Level of detail the log will show. 0 (show arbitrable matches above threshold) and 1 (show all arbitrable matches) are the ones reccomended for normal uses. The other ones have more of a debug purpose.

*  **threshold**: Percentage of guaranteed earnings you want to show at verbosity 0. 

*  **bet size**: Amount to bet in order to see the returns.

You can also change the region of the betting houses. Changing `markets` or `odds_format` will break the application.

### Matches

The program will try to get all the head to head matches for all the sports in the api. Each sport will be saved to a file (`<SPORT_NAME>.json`) in the `jsons` folder. If a sport file is present in the folder, the program won't fetch the odds from the api and will use the existing file. **In order to get fresh odds you need to delete the files you want to refresh.**

Some example use cases will be:
* 1.- **Refresh the whole list**. You'll delete the `jsons` folder in this case and all sports will be re-fetched.

* 2.- **Polling La liga**. You'll delete `jsons/soccer_spain_la_liga.json` and re-run the program. This will use just one API call for each refresh.