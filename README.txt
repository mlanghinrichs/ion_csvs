=== USING THE SCRIPT ===

Export three .csv files from ION:
1. Reports -> Imp Reports -> Product Buylist History Report
	- Set Date Start and Date End, then hit filter, then export
2. Catalog -> Products
	- Set Quantity > 0, filter, export
3. Catalog -> Products
	- Reset any other filter
	- select "New In Stock" under Advanced Filters
	- Filter, export

Run apply_new_in_stock_filter.py and select all three CSV files in the file dialog that appears.
Your exported csv with the appropriate filters added and removed will appear in the same directory as the script.
Please always check output.csv to make sure the content looks correct!

=== TROUBLESHOOTING ===

- You can exclude the csv containing cards that already have the New In Stock filter and just add the filter to the new cards.
- The script doesn't currently generate error output consistently if something unexpected happened during running, so check the output csv before you import it into ION.
- The script automatically determines which csv is which based on the data it expects from those specific exports, so make sure you load the correct files!