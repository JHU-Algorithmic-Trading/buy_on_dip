# First time setup...  
On Windows cmd line:
```
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt 
```
On Linux:
```
python -m venv venv
source venv\bin\activate
pip install -r requirements.txt 
```

# Run
## Basic
Once your environment is set up, make sure your environment is sourced via `venv\Scripts\activate` on Windows cmd line or `source venv\bin\activate` on Linux (see above).  

The most basic file to run to test out the strategy is `main.py`. Make any desired edits to the input section at the top of the file, and run with  
```
python main.py > ticker_backtest.txt
```
You are free to change the name of the text file, as that will simply dump all print statements to it.  

## Advanced
For a more detailed approach, I've written a script to grab the top n stock losers of the day, given some input threshold, and run the same strategy backtest as above on each stock. By default, the script will dump results in a folder called `backtests/` under a subfolder with today's date. To change the parameters of this backtest, simply edit the capitalized variables at the top of `src.py`. Then run the following:
```
python src.py
```
The program will create an `inputs.json` file with all the inputs of the run for reproducability, and a folder for each ticker. Under each ticker subfolder, it will create 3 files - `backtest.json`, `backtest.txt`, and `metrics.json`.  

`backtest.txt` gives the same printed output as the Basic run detailed above (walks you through exactly what the algorithm is doing). `backtest.json` puts this same information into a json file for easier parsin. `metrics.json` contains all the useful metrics of that backtest, which can easily be used for future trade decisions.



