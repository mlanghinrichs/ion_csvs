import csv, re, os


def dump_csv(filename):
    """Return list of dicts mirroring table structure in filename."""
    file = []

    this_csv_name="old_in_stock"

    try:
        with open(filename) as csvfile:
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
                    elif reader_list[0][i] == "name":
                        rowdict["product_name"] = row[i]
                if "filters" in rowdict and "12" not in rowdict["filters"] and this_csv_name == "old_in_stock":
                    print(rowdict)
                    this_csv_name = "in_stock"
                file.append(rowdict)
    except FileNotFoundError:
        print(f"File {filename} not found! Perhaps you named it improperly?")
    except IndexError as ierror:
        print(f"Something went wrong with indexing in dump_csv!")
        print(ierror)

    file.append(this_csv_name)
    return file


def change_filters(filter_string, filter_id, add=True):
    """Add or remove filter {filter_id} to filter_string."""
    filters = filter_string.split(",")
    if add:
        filters.append(filter_id)
        filters.sort()
    else:
        if filter_id in filters: filters.remove(filter_id)
    return ",".join(filters)


# --- Initial import/preprocessing of CSVs ---
output_csv = []
dumps = []
for filename in os.listdir("input/"):
    dumps.append(dump_csv("input/" + filename))

while (len(dumps) < 3):
    dumps.append(["old_in_stock"])

for csvfile in dumps:
    if csvfile[-1] == "new_in_stock":
        new_in_stock = csvfile
        new_in_stock.pop(-1)
    elif csvfile[-1] == "old_in_stock":
        old_in_stock = csvfile
        old_in_stock.pop(-1)
    else:
        in_stock = csvfile
        in_stock.pop(-1)

# --- Remove tag '12' from anything old-in-stock and save *just those* to the eventual output ---
for row in old_in_stock:
    row["filters"] = change_filters(row["filters"], "12", False)

output_csv.extend(old_in_stock)

# --- Search for "new in stock" in "in stock" and pull their existing tags ---
in_stock.sort(key=lambda x: x["model"])
new_in_stock.sort(key=lambda x: x["model"])

for new_item in new_in_stock:
    for in_i in range(0, len(in_stock)):
        if new_item["model"] == in_stock[in_i]["model"]:
            new_item["filters"] = in_stock[in_i]["filters"]
            # in_stock = in_stock[in_i:]
            break
    if "filters" not in new_item:
        print(f"Didn't find item {new_item['product_name']} in in-stock list.")

# Filter out cards which didn't get a filter added, because they weren't on the "in_stock" list.
new_in_stock = list(filter(lambda x: "filters" in x, new_in_stock))

# --- Add tag 12 to the new in stock items, add new in stock items to output ---
for row in new_in_stock:
    row["filters"] = change_filters(row["filters"], "12")
output_csv.extend(new_in_stock)

# --- Export all to CSV ---
with open("output/output.csv", "w", newline="") as csvfile:
    fieldnames = ["product_name", "model", "filters"]
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(output_csv)

