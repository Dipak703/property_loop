# Data Folder

Place your CSV files here:

- `trades.csv` - Must contain at least a `PortfolioName` column
- `holdings.csv` - Must contain at least `PortfolioName` and `PL_YTD` columns

## Expected CSV Format

### trades.csv
```csv
PortfolioName,OtherColumn1,OtherColumn2,...
Fund A,value1,value2,...
Fund A,value3,value4,...
Fund B,value5,value6,...
```

### holdings.csv
```csv
PortfolioName,PL_YTD,OtherColumn1,...
Fund A,1000.50,value1,...
Fund A,500.25,value2,...
Fund B,-200.75,value3,...
```

The chatbot will automatically:
- Count rows in `trades.csv` grouped by `PortfolioName` for trade counts
- Count rows in `holdings.csv` grouped by `PortfolioName` for holding counts
- Sum `PL_YTD` in `holdings.csv` grouped by `PortfolioName` for performance
