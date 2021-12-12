import json
import pandas as pd
import numpy as np

pd.options.mode.chained_assignment = None


class BasketPricer(object):
    def get_discounts(self, catalog_file, offer_file, basket_file):
        priced_basket = self.create_priced_basket(catalog_file, basket_file)
        basket_wdiscounts = self.apply_offers(
            priced_basket,
            offer_types=json.loads("".join(open(offer_file, "r").readlines())),
        )
        self.print_results(
            self.get_totals(basket_wdiscounts)[0],
            self.get_totals(basket_wdiscounts)[1],
            self.get_totals(basket_wdiscounts)[2],
        )

    def get_totals(self, basket_wdiscounts):
        if basket_wdiscounts.shape[0] >= 1:
            sub_total = round(basket_wdiscounts["Sub Total"].sum(), 2)
            discount = round(basket_wdiscounts["Discount"].sum(), 2)
            total = round(basket_wdiscounts["Sub Total"].sum() - discount, 2)
            if total < 0:
                total = 0
        else:
            sub_total = 0
            discount = 0
            total = 0
        return (sub_total, discount, total)

    def create_priced_basket(self, catalog_file, basket_file):
        catalog = pd.read_csv(catalog_file)
        basket = pd.read_csv(basket_file)
        priced_basket = pd.merge(basket, catalog, on=["Item"], how="left")
        priced_basket["Sub Total"] = (
            priced_basket.Quantity * priced_basket.Price
        )
        return priced_basket

    def print_results(self, sub_total, discount, total):
        print("sub-total: £{0:.2f}".format(sub_total))
        print("discount: £{0:.2f}".format(discount))
        print("total: £{0:.2f}".format(total))

    def apply_offers(self, priced_basket, offer_types):
        for offer_type in offer_types:
            for offer in offer_types[offer_type]:
                applicable_items_temp = priced_basket.loc[
                    priced_basket["CategoryCode"] == offer["category"]
                ]
                applicable_items = applicable_items_temp[
                    ["Item", "Quantity", "Price", "CategoryCode", "Sub Total"]
                ]
                if applicable_items.shape[0] >= 1:
                    if offer_type == "multi_buy_free":
                        discounted_multibuy = self.get_multi_buy_discounts(
                            applicable_items, offer
                        )
                        priced_basket = self.merge_discount_col(
                            pd.merge(
                                priced_basket,
                                discounted_multibuy,
                                on=["Item"],
                                how="left",
                                suffixes=("_left", "_right"),
                            )
                        )
                    elif offer_type == "general_discount":
                        general_discount = self.get_general_discounts(
                            applicable_items, offer
                        )
                        priced_basket = self.merge_discount_col(
                            pd.merge(
                                priced_basket,
                                general_discount,
                                on=["Item"],
                                how="left",
                                suffixes=("_left", "_right"),
                            )
                        )
                    elif offer_type == "multi_buy_cheapest_free":
                        multi_cheapest = self.get_multi_cheapest_discounts(
                            applicable_items, offer
                        )
                        priced_basket = self.merge_discount_col(
                            pd.merge(
                                priced_basket,
                                multi_cheapest,
                                on=["Item"],
                                how="left",
                                suffixes=("_left", "_right"),
                            )
                        )
        priced_basket = priced_basket.fillna(0)
        return priced_basket

    def merge_discount_col(self, priced_basket):
        if (
            "Discount_left" in priced_basket.columns
            and "Discount_right" in priced_basket.columns
        ):
            priced_basket = priced_basket.fillna(0)
            priced_basket["Discount"] = (
                priced_basket["Discount_left"]
                + priced_basket["Discount_right"]
            )
            priced_basket = priced_basket.drop("Discount_left", axis=1)
            priced_basket = priced_basket.drop("Discount_right", axis=1)
        return priced_basket

    def get_multi_cheapest_discounts(self, applicable_items, offer):
        discount_quantity = int(
            sum(applicable_items["Quantity"]) / offer["qualifying_quantity"]
        )
        discount_amount = min(applicable_items["Price"]) * discount_quantity
        if applicable_items.shape[0] == 1:
            discount_item = applicable_items[
                applicable_items["Price"] == discount_amount
            ]
        else:
            discount_item = applicable_items[
                applicable_items["Price"] == discount_amount
            ].iloc[[0]]
        discount_item["Discount"] = discount_amount
        applicable_items = pd.merge(
            applicable_items,
            discount_item[["Item", "Discount"]],
            on="Item",
            how="left",
        )
        return applicable_items[["Item", "Discount"]]

    def get_general_discounts(self, applicable_items, offer):
        applicable_items["Discount"] = round(
            applicable_items["Sub Total"] * offer["discount"], 2
        )
        return applicable_items[["Item", "Discount"]]

    def get_multi_buy_discounts(self, applicable_items, offer):
        applicable_items["Discount"] = applicable_items["Quantity"] / (
            offer["qualifying_quantity"] + offer["amount_free"]
        )
        applicable_items["Discount"] = applicable_items["Discount"].apply(
            np.floor
        )
        applicable_items["Discount"] = (
            applicable_items["Discount"] * applicable_items["Price"]
        )
        return applicable_items[["Item", "Discount"]]


if __name__ == "__main__":
    basket_pricer = BasketPricer()
    basket_pricer.get_discounts(
        catalog_file="../test_data/catalog.csv",
        offer_file="../test_data/offers.json",
        basket_file="../test_data/basket_3.csv",
    )
