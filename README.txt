=== USING THE SCRIPT ===

Export two .csv files from ION:
1. Reports -> Imp Reports -> Product Buylist History Report
	- Set Date Start and Date End, then hit filter, then export
2. Reports -> Imp Reports -> Export Inventory (Conditions)

Run apply_new_in_stock_filter.py and select all both CSV files in the file dialog that appears.
Your exported csv with the appropriate tags added and removed will appear in the same directory as the script.
Please always check output.csv to make sure the content looks correct!

=== TROUBLESHOOTING ===

- The script doesn't currently generate error output consistently if something unexpected happened during running, so check the output csv before you import it into ION.
- The script automatically determines which csv is which based on the data it expects from those specific exports, so make sure you load the correct files!
