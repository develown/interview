import pytest
import sys
import pandas as pd
import json
from mock import patch

sys.path.insert(1, "../scripts")
from basket_pricer import BasketPricer


@pytest.fixture()
def basket_pricer():
    return BasketPricer()


def test_create_priced_basket(basket_pricer):
    priced_basket = basket_pricer.create_priced_basket(
        "../test_data/catalog.csv", "../test_data/basket_1.csv"
    )
    assert priced_basket.shape == (10, 5)
    assert sum(priced_basket["Sub Total"]) == 33.89


def test_print(basket_pricer, capfd):
    basket_pricer.print_results(0.00, 0.00, 0.00)
    out, err = capfd.readouterr()
    expected_output = "sub-total: £0.00\ndiscount: £0.00\ntotal: £0.00\n"
    assert out == expected_output


def test_get_totals(basket_pricer):
    priced_basket_wdiscount = pd.DataFrame(
        [["Baked Beans (value)", 3, 0.99, 1, 2.97, 0.99]],
        columns=[
            "Item",
            "Quantity",
            "Price",
            "CategoryCode",
            "Sub Total",
            "Discount",
        ],
    )
    totals = basket_pricer.get_totals(priced_basket_wdiscount)
    assert totals == (2.97, 0.99, 1.98)
    priced_basket_negative = pd.DataFrame(
        [["Baked Beans (value)", 3, 0.99, 1, 2.97, 4.00]],
        columns=[
            "Item",
            "Quantity",
            "Price",
            "CategoryCode",
            "Sub Total",
            "Discount",
        ],
    )
    totals = basket_pricer.get_totals(priced_basket_negative)
    assert totals == (2.97, 4.0, 0)


def test_apply_offers(basket_pricer):
    priced_basket = pd.DataFrame(
        [["Baked Beans (value)", 3, 0.99, 1, 2.97]],
        columns=["Item", "Quantity", "Price", "CategoryCode", "Sub Total"],
    )
    multi_discounts = pd.DataFrame(
        [["Baked Beans (value)", 0.99]], columns=["Item", "Discount"]
    )
    offers = json.loads(
        "".join(open("../test_data/offers.json", "r").readlines())
    )
    with patch.object(
        basket_pricer, "get_multi_buy_discounts", return_value=multi_discounts
    ) as mock_call_multi:
        with patch.object(
            basket_pricer, "get_general_discounts", return_value=pd.DataFrame()
        ) as mock_call_general:
            with patch.object(
                basket_pricer,
                "get_multi_cheapest_discounts",
                return_value=pd.DataFrame(),
            ) as mock_call_cheapest:
                priced_basket_wdiscount = basket_pricer.apply_offers(
                    priced_basket, offers
                )
                assert priced_basket_wdiscount.shape == (1, 6)
                assert sum(priced_basket_wdiscount["Discount"]) == 0.99


def test_merge_discount_col(basket_pricer):
    applicable_items_suffix = pd.DataFrame(
        [["Shampoo (Large)", 2, 1.5, 8, 3.0, 0.0, 1.0]],
        columns=[
            "Item",
            "Quantity",
            "Price",
            "CategoryCode",
            "Sub Total",
            "Discount_left",
            "Discount_right",
        ],
    )
    applicable_items = basket_pricer.merge_discount_col(
        applicable_items_suffix
    )
    assert applicable_items.shape == (1, 6)
    assert sum(applicable_items["Discount"]) == 1.0
    applicable_items_nosuffix = pd.DataFrame(
        [["Shampoo (Large)", 2, 1.5, 8, 3.0, 1.0]],
        columns=[
            "Item",
            "Quantity",
            "Price",
            "CategoryCode",
            "Sub Total",
            "Discount",
        ],
    )
    applicable_items = basket_pricer.merge_discount_col(
        applicable_items_nosuffix
    )
    assert applicable_items.shape == (1, 6)
    assert sum(applicable_items["Discount"]) == 1.0


def test_get_multi_cheapest_discounts(basket_pricer):
    applicable_items_sameprice = pd.DataFrame(
        [
            ["Shampoo (Large)", 2, 1.5, 8, 3.0],
            ["Shampoo (Medium)", 1, 1.5, 8, 1.5],
        ],
        columns=["Item", "Quantity", "Price", "CategoryCode", "Sub Total"],
    )
    offer = json.loads(
        "".join(open("../test_data/offers.json", "r").readlines())
    )["multi_buy_cheapest_free"][0]
    applicable_items = basket_pricer.get_multi_cheapest_discounts(
        applicable_items_sameprice, offer
    ).fillna(0)
    assert applicable_items.shape == (2, 2)
    assert sum(applicable_items["Discount"]) == 1.5
    applicable_items_diffrentprice = pd.DataFrame(
        [
            ["Shampoo (Large)", 2, 1.5, 8, 3.0],
            ["Shampoo (Medium)", 1, 1, 8, 1],
        ],
        columns=["Item", "Quantity", "Price", "CategoryCode", "Sub Total"],
    )
    offer = json.loads(
        "".join(open("../test_data/offers.json", "r").readlines())
    )["multi_buy_cheapest_free"][0]
    applicable_items = basket_pricer.get_multi_cheapest_discounts(
        applicable_items_diffrentprice, offer
    ).fillna(0)
    assert applicable_items.shape == (2, 2)
    assert sum(applicable_items["Discount"]) == 1


def test_general_discounts(basket_pricer):
    applicable_items_nodiscount = pd.DataFrame(
        [["Sardines", 2, 1.89, 3, 3.78]],
        columns=["Item", "Quantity", "Price", "CategoryCode", "Sub Total"],
    )
    offer = json.loads(
        "".join(open("../test_data/offers.json", "r").readlines())
    )["general_discount"][0]
    applicable_items = basket_pricer.get_general_discounts(
        applicable_items_nodiscount, offer
    )
    assert applicable_items.shape == (1, 2)
    assert sum(applicable_items["Discount"]) == 0.94


def test_get_multi_buy_discounts(basket_pricer):
    applicable_items_nodiscount = pd.DataFrame(
        [["Baked Beans (value)", 2, 0.99, 1, 1.98]],
        columns=["Item", "Quantity", "Price", "CategoryCode", "Sub Total"],
    )
    offer = json.loads(
        "".join(open("../test_data/offers.json", "r").readlines())
    )["multi_buy_free"][0]
    applicable_items = basket_pricer.get_multi_buy_discounts(
        applicable_items_nodiscount, offer
    )
    assert applicable_items.shape == (1, 2)
    assert sum(applicable_items["Discount"]) == 0.0
    applicable_items_discount = pd.DataFrame(
        [["Baked Beans (value)", 3, 0.99, 1, 1.98]],
        columns=["Item", "Quantity", "Price", "CategoryCode", "Sub Total"],
    )
    applicable_items = basket_pricer.get_multi_buy_discounts(
        applicable_items_discount, offer
    )
    assert applicable_items.shape == (1, 2)
    assert sum(applicable_items["Discount"]) == 0.99
