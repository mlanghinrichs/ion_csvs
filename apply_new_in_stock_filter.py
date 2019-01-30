from tkinter.filedialog import askopenfilenames
import csv
import os


class CSVProcessor():

    def __init__(self, filter_to_change_id="85"):
        self.filter = filter_to_change_id
        self.raw_data=[]
        self.result = []
        self.file_names = ()
        # Containers for three input CSVs
        self.new_in_stock = []
        self.old_in_stock = []
        self.in_stock = []

    def main(self):
        self.get_input_file_names()
        self.process_input_csvs()
        self.remove_old_tags()
        self.pull_existing_tags()
        self.remove_out_of_stock_new_cards()
        self.add_filter_to_new_cards()
        self.export()

    def dump_csv(self, file_name):
        """Dump into raw_data a list of dicts mirroring the table structure in file_name."""
        file = []
        # Default to old in stock, then if you find any without the filter you can switch this to being 'in stock'
        this_csv_name = "old_in_stock"
        try:
            with open(file_name) as csvfile:
                reader = csv.reader(csvfile)
                reader_list = list(reader)
                for row in reader_list:
                    # Skip header row, which always contains "model"
                    if "model" in row:
                        if row[0] == "name":
                            this_csv_name = "new_in_stock"
                        continue
                    # Put each row into a dict with values indexed by their header
                    rowdict = {}
                    for i in range(0, len(row)):
                        if reader_list[0][i] in ("product_name", "model", "filters"):
                            rowdict[reader_list[0][i]] = row[i]
                        # Fix the buylist report's 'name' header into the standard 'product_name' header
                        elif reader_list[0][i] == "name":
                            rowdict["product_name"] = row[i]
                    # If this row's item doesn't have the new in stock filter already, this must be the in-stock file
                    if ("filters" in rowdict
                            and self.filter not in rowdict["filters"]
                            and this_csv_name == "old_in_stock"):
                        this_csv_name = "in_stock"
                    file.append(rowdict)
        except FileNotFoundError:
            print(f"File {file_name} not found! Perhaps you named it improperly?")
        except IndexError as ierror:
            print(f"Something went wrong with indexing in dump_csv!")
            print(ierror)
        # Add which csv this is as a footer to be read and popped off later
        file.append(this_csv_name)
        self.raw_data.append(file)

    def get_input_file_names(self):
        """Open file dialog and stow chosen filenames in self.file_names tuple."""
        self.file_names = askopenfilenames(initialdir=os.path.abspath(os.sep),
                                           title="Select *all three* csv files!",
                                           filetypes=(("csv files", "*.csv"), ("all files", "*.*")))

    def process_input_csvs(self):
        """Dump the CSVs into raw_data, then check their contents to name each as the appropriate list."""
        for filename in self.file_names:
            self.dump_csv(filename)
        for csvfile in self.raw_data:
            def assign(obj):
                obj = csvfile
                obj.pop(-1)
            if csvfile[-1] == "new_in_stock":
                assign(self.new_in_stock)
            elif csvfile[-1] == "old_in_stock":
                assign(self.old_in_stock)
            else:
                assign(self.in_stock)

    def remove_old_tags(self):
        """Remove the selected filter tag from cards in the 'old in stock' list."""
        for row in self.old_in_stock:
            row["filters"] = CSVProcessor.change_filters(row["filters"], self.filter, False)
        self.result.extend(self.old_in_stock)

    def pull_existing_tags(self):
        """Copy filter tags from 'in stock' list to 'new in stock' list."""
        self.in_stock.sort(key=lambda x: x["model"])
        self.new_in_stock.sort(key=lambda x: x["model"])
        for new_item in self.new_in_stock:
            for in_i in range(0, len(self.in_stock)):
                if new_item["model"] == self.in_stock[in_i]["model"]:
                    new_item["filters"] = self.in_stock[in_i]["filters"]
                    self.in_stock = self.in_stock[in_i:]
                    break
            if "filters" not in new_item:
                print(f"Didn't find item {new_item['product_name']} in in-stock list.")

    def remove_out_of_stock_new_cards(self):
        """Remove any cards from self.new_in_stock which don't have a 'filters' column."""
        self.new_in_stock = list(filter(lambda x: "filters" in x, self.new_in_stock))

    def add_filter_to_new_cards(self):
        """Add self.filter to the 'filters' string of each card in self.new_in_stock."""
        for row in self.new_in_stock:
            row["filters"] = CSVProcessor.change_filters(row["filters"], self.filter)
        self.result.extend(self.new_in_stock)

    def export(self):
        """Write the contents of self.result to file output.csv in the local directory."""
        with open("output.csv", "w", newline='') as csvfile:
            fieldnames = ["product_name", "model", "filters"]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self.result)

    @staticmethod
    def change_filters(filter_string, filter_id, add=True):
        """Add or remove filter {filter_id} to filter_string."""
        filters = filter_string.split(",")
        if add:
            filters.append(filter_id)
            filters.sort()
        else:
            if filter_id in filters:
                filters.remove(filter_id)
        return ",".join(filters)


if __name__ == "__main__":
    processor = CSVProcessor()
    processor.main()

