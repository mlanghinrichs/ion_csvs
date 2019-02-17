from tkinter.filedialog import askopenfilenames
import csv
import os
import time


class CSVProcessor:

    def __init__(self, *, filter_to_change_id="85",
                 path=os.path.abspath(os.sep)):
        self.load_message = "Select *all three* csv files!"
        self.path = path
        self.filter = filter_to_change_id
        self.raw_data = []
        self.result = []
        self.cards_sold = 0
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
        self.ensure_unique_entries()
        self.export()

    def dump_csv(self, file_name):
        """Dump into raw_data a list of dicts mirroring the table structure in
        file_name."""
        file = []
        # Default to old in stock, then if you find any without the filter you
        # can switch this to being 'in stock'
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
                    # Put each row into a dict with values indexed by their
                    # header
                    rowdict = {}
                    for i in range(0, len(row)):
                        if reader_list[0][i] in ("product_name", "model",
                                                 "filters"):
                            rowdict[reader_list[0][i]] = row[i]
                        # Rename the buylist report's 'name' header to the
                        # standard 'product_name' header
                        elif reader_list[0][i] == "name":
                            rowdict["product_name"] = row[i]
                    # If this row's item doesn't have the new in stock filter
                    # already, this must be the in-stock file
                    if ("filters" in rowdict
                            and self.filter not in rowdict["filters"]
                            and this_csv_name == "old_in_stock"):
                        this_csv_name = "in_stock"
                    file.append(rowdict)
        except FileNotFoundError:
            print(f"File {file_name} not found!")
        except IndexError as ierror:
            print(f"Something went wrong with indexing in dump_csv!")
            print(ierror)
        # Add which csv this is as a footer to be read and popped off later
        file.append(this_csv_name)
        self.raw_data.append(file)

    def confirm_identical_filters_in_results(self, model):
        """Return whether all instances of card with id 'model' have identical
        'filter' values."""
        first_tags = ""
        for card in CSVProcessor.cards_in_csv(self.result, "model", model):
            if not first_tags:
                first_tags = card["filters"]
            elif first_tags != card["filters"]:
                return False
        return True

    # Begin main() program logic
    def get_input_file_names(self):
        """Open file dialog and stow chosen files in self.file_names tuple."""
        self.file_names = askopenfilenames(initialdir=self.path,
                                           title=self.load_message,
                                           filetypes=(("csv files", "*.csv"),
                                                      ("all files", "*.*")))

    # TODO improve error checking
    def process_input_csvs(self):
        """Dump the CSVs into raw_data, then check their contents to name each
        as the appropriate list."""
        for filename in self.file_names:
            self.dump_csv(filename)
        names = [file[-1] for file in self.raw_data]
        if len(set(names)) != len(names):
            raise NameError("Multiple imported CSV files look the same!")
        for csvfile in self.raw_data:
            if csvfile[-1] == "new_in_stock":
                self.new_in_stock = csvfile
                self.new_in_stock.pop(-1)
            elif csvfile[-1] == "old_in_stock":
                self.old_in_stock = csvfile
                self.old_in_stock.pop(-1)
            else:
                self.in_stock = csvfile
                self.in_stock.pop(-1)

    def remove_old_tags(self):
        """Remove selected filter tag from cards in the 'old in stock' list."""
        for row in self.old_in_stock:
            card_in_new_in_stock = CSVProcessor.card_in_csv(
                self.new_in_stock,
                "model",
                row["model"]
            )
            # If this old-in-stock card isn't also a new-in-stock card, remove
            # the new-in-stock filter
            if not card_in_new_in_stock:
                row["filters"] = CSVProcessor.change_filters(row["filters"],
                                                             self.filter,
                                                             False)
                print(f"Removing tag {self.filter} from {row['product_name']}")
            # If this card IS also a new-in-stock card, leave it as-is and
            # remove it from the new-in-stock list
            else:
                self.new_in_stock.remove(card_in_new_in_stock)
                print(f"Removing {card_in_new_in_stock['product_name']}.")
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
                print(f"Didn't find item {new_item['product_name']}.")

    def remove_out_of_stock_new_cards(self):
        """Remove cards from new_in_stock which don't have 'filters' column.

        This is because in pull_existing_tags we added a 'filters' column
        to any cards which WERE in in_stock."""
        before_len = len(self.new_in_stock)
        self.new_in_stock = list(filter(lambda x: "filters" in x,
                                        self.new_in_stock))
        after_len = len(self.new_in_stock)
        self.cards_sold = before_len - after_len
        print(f"Sold {self.cards_sold} unique new cards since intake.")

    def add_filter_to_new_cards(self):
        """Add filter to the 'filters' str of each card in new_in_stock."""
        for row in self.new_in_stock:
            row["filters"] = CSVProcessor.change_filters(row["filters"],
                                                         self.filter)
        self.result.extend(self.new_in_stock)

    # TODO Determine why there are duplicates in the first place
    # - this is a hotfix
    def ensure_unique_entries(self):
        """Clear duplicates out of self.result."""
        list_of_models = [row["model"] for row in self.result]
        for model in set(list_of_models):
            if CSVProcessor.all_unique_by_model(self.result):
                break
            while list_of_models.count(model) > 1:
                if not self.confirm_identical_filters_in_results(model):
                    raise UserWarning("Tried to remove duplicate cards"
                                      + "with different filters!")
                list_of_models.remove(model)
                self.result.remove(CSVProcessor.card_in_csv(self.result,
                                                            "model",
                                                            model))

    def export(self):
        """Write the contents of self.result to newinstock_{timestamp}.csv."""
        with open(
                "newinstock_" + time.strftime("%Y-%m-%d_%H%M") + ".csv",
                "w", newline=''
                ) as csvfile:
            fieldnames = ["product_name", "model", "filters"]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self.result)

    @staticmethod
    def change_filters(filter_string, filter_id, add=True):
        """Add or remove filter {filter_id} to filter_string."""
        filters = filter_string.split(",")
        if add and filter_id not in filters:
            filters.append(filter_id)
            filters.sort()
        elif not add and filter_id in filters:
            if filter_id in filters:
                filters.remove(filter_id)
        return ",".join(filters)

    @staticmethod
    def card_in_csv(csvfile, key, value):
        """Check if a card is present in a CSV and return it if so."""
        for row in csvfile:
            if row[key] == value:
                return row
        return {}

    @staticmethod
    def cards_in_csv(csvfile, key, value):
        """Return all cards in a csv with card[key] == value."""
        result = []
        for row in csvfile:
            if row[key] == value:
                result.append(row)
        return result

    @staticmethod
    def all_unique_by_model(csvfile):
        """Return whether a csvfile has only one entry per model id."""
        models = [row["model"] for row in csvfile]
        return len(set(models)) == len(models)


class CSVTagProcessor(CSVProcessor):

    def __init__(self, tag_to_add="New In Stock",
                 path=os.path.abspath(os.sep)):
        super().__init__(path=path)
        self.load_message = "Select *both* csv files!"
        self.tag = tag_to_add

    def main(self):
        self.get_input_file_names()
        self.process_input_csvs()
        self.remove_old_tags()
        self.add_tag_to_new_cards()
        self.ensure_unique_entries()
        self.export()

    def dump_csv(self, file_name):
        """Dump a list of dicts mirroring the table structure in file_name."""
        file = []
        # Default to old in stock, then if you find any without the filter you
        # can switch this to being 'in stock'
        this_csv_name = ""
        try:
            with open(file_name) as csvfile:
                reader = csv.reader(csvfile)
                reader_list = list(reader)
                for row in reader_list:
                    # Skip header row, which always contains "model"
                    if "model" in row:
                        this_csv_name = "new_in_stock"
                        continue
                    elif "product_model" in row:
                        this_csv_name = "in_stock"
                        continue
                    # Put each row into a dict with values indexed by their
                    # header
                    rowdict = {}
                    for i in range(0, len(row)):
                        header = reader_list[0][i]
                        value = row[i]
                        if header in ("product_name", "model"):
                            rowdict[header] = value
                        # Rename the buylist report's 'name' header to the
                        # standard 'product_name' header
                        elif header == "name":
                            rowdict["product_name"] = value
                        elif header == "product_model":
                            rowdict["model"] = value
                    # Write the finished Row dict to 'file'
                    file.append(rowdict)
        except FileNotFoundError:
            print(f"File {file_name} not found!")
        except IndexError as ierror:
            print(f"Something went wrong with indexing in dump_csv!")
            print(ierror)
        # Add which csv this is as a footer to be read and popped off later
        file.append(this_csv_name)
        self.raw_data.append(file)

    def remove_old_tags(self):
        """Remove the selected tag from cards in the 'old in stock' list."""
        for row in self.in_stock:
            card_in_new_in_stock = CSVProcessor.card_in_csv(
                self.new_in_stock,
                "model",
                row["model"]
            )
            # If this old-in-stock card isn't also a new-in-stock card, remove
            # the new-in-stock filter
            if not card_in_new_in_stock:
                row["product_tag"] = ""
            # If this card IS also a new-in-stock card, leave it as-is and
            # remove it from the new-in-stock list
            else:
                row["product_tag"] = "New In Stock"
                self.new_in_stock.remove(card_in_new_in_stock)
        self.result.extend(self.in_stock)

    def add_tag_to_new_cards(self):
        """Add self.tag to the tags string of each card in new_in_stock."""
        for row in self.new_in_stock:
            row["product_tag"] = "New In Stock"
        self.result.extend(self.new_in_stock)

    def ensure_unique_entries(self):
        """Clear duplicates out of self.result."""
        print(CSVProcessor.all_unique_by_model(self.result))

    def export(self):
        """Write self.result to newinstock_{timestamp}.csv."""
        with open("newinstock_" + time.strftime(
                "%Y-%m-%d_%H%M") + ".csv",
                "w",
                newline=''
                ) as csvfile:
            fieldnames = ["product_name", "model", "product_tag"]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self.result)


class CSVFilterRemover(CSVProcessor):

    def __init__(self, filter_to_remove="85", path=os.path.abspath(os.sep)):
        self.path = path
        self.filter = filter_to_remove
        self.load_message = "Select old_in_stock file to remove filter."
        self.raw_data = []
        self.file_names = ()
        self.result = []

    def main(self):
        self.get_input_file_names()
        self.process_csv()
        self.remove_old_tags()
        self.export()

    def process_csv(self):
        self.dump_csv(self.file_names[0])
        self.old_in_stock = self.raw_data[0]
        self.old_in_stock.pop(-1)

    def remove_old_tags(self):
        """Remove the selected filter tag from cards in 'old in stock' list."""
        for row in self.old_in_stock:
            row["filters"] = CSVProcessor.change_filters(row["filters"],
                                                         self.filter,
                                                         False)
        self.result.extend(self.old_in_stock)


if __name__ == "__main__":
    processor = CSVTagProcessor()
    processor.main()
