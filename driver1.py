import tkinter as tk
from tkinter import messagebox
import json

class AssociationModel:
    def __init__(self, association_rules_file):
        with open(association_rules_file, 'r') as f:
            self.association_rules = json.load(f)
    
    def find_associated_products(self, product_name):
        associated_products = []
        for rule in self.association_rules:
            if product_name in rule['antecedents']:
                associated_products.extend(rule['consequents'])
        return list(set(associated_products))

class GUI:
    def __init__(self, master, model):
        self.master = master
        self.model = model

        self.master.title("Market Basket Analysis")

        self.label = tk.Label(master, text="Enter Product Name:")
        self.label.pack()

        self.entry = tk.Entry(master)
        self.entry.pack()

        self.button = tk.Button(master, text="Find Associated Products", command=self.find_associated)
        self.button.pack()

        self.output_label = tk.Label(master, text="")
        self.output_label.pack()

    def find_associated(self):
        product_name = self.entry.get().strip()
        if product_name:
            associated_products = self.model.find_associated_products(product_name)
            if associated_products:
                output_text = "Associated Products:\n" + "\n".join(associated_products)
            else:
                output_text = "No associated products found."
            self.output_label.config(text=output_text)
        else:
            messagebox.showerror("Error", "Please enter a product name.")

if __name__ == "__main__":
    # Load association model
    association_rules_file = 'association_rules.json'
    model = AssociationModel(association_rules_file)

    # Create Tkinter window
    root = tk.Tk()
    app = GUI(root, model)
    root.mainloop()
