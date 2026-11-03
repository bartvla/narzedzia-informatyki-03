from sqlalchemy.util.cython import double

from pydantic import BaseModel
from typing import Dict, List





import json

class Parameters(BaseModel):
    apartments_json_path: str = 'data/apartments.json'
    tenants_json_path: str = 'data/tenants.json'
    transfers_json_path: str = 'data/transfers.json'
    bills_json_path: str = 'data/bills.json'

class Room(BaseModel):
    name: str
    area_m2: float

class ApartmentSettlement(BaseModel):
    name: str
    room: str
    rent_pln: float
    date_agreement_from: str
    date_agreement_to: str

    @staticmethod
    def from_json_file(file_path: str):
            data = None
            with open(file_path, 'r') as file:
                data = json.load(file)
            assert isinstance(data, dict), "Expected a dictionary of tenants"
            return {key: {"rent_pln": tenant["rent_pln"], "room":tenant["room"],"name":tenant["name"]} for key, tenant in data.items()}

class Apartment(BaseModel):
    key: str
    name: str
    location: str
    area_m2: float
    rooms: Dict[str, Room]

    @staticmethod
    def from_json_file(file_path: str) -> Dict[str,'Apartment']:
        data = None
        with open(file_path, 'r') as file:
            data = json.load(file)
        assert isinstance(data, dict), "Expected a dictionary of tenants"
        return {key: Apartment(**apartment) for key, apartment in data.items()}
    
class Tenant(BaseModel):
    name: str
    apartment: str
    room: str
    rent_pln: float
    deposit_pln: double
    date_agreement_from: str
    date_agreement_to: str

    @staticmethod
    def from_json_file(file_path: str) -> Dict[str,'Tenant']:
        data = None
        with open(file_path, 'r') as file:
            data = json.load(file)
        assert isinstance(data, dict), "Expected a dictionary of tenants"
        return {key: Tenant(**tenant) for key, tenant in data.items()}

class Transfer(BaseModel):
    amount_pln: float
    date: str
    settlement_year: int | None
    settlement_month: int | None
    tenant: str

    @staticmethod
    def from_json_file(file_path: str) -> List['Transfer']:
        data = None
        with open(file_path, 'r') as file:
            data = json.load(file)
        assert isinstance(data, list), "Expected a list of transfers"
        return [Transfer(**transfer) for transfer in data]

class TenantSettlement(BaseModel):
    tenant: str
    apartment_settlement: str
    year: int
    month: int
    rent_pln: float
    bills_pln: float
    total_due_pln: float
    total_transfers_pln: float
    balance_pln: float

class Bill(BaseModel):
    amount_pln: float
    date_due: str
    apartment: str
    settlement_year: int
    settlement_month: int
    type: str

    @staticmethod
    def from_json_file(file_path: str) -> List['Bill']:
        data = None
        with open(file_path, 'r') as file:
            data = json.load(file)
        assert isinstance(data, list), "Expected a list of bills"
        return [Bill(**bill) for bill in data]

class Manager:
    def __init__(self, parameters: Parameters):
        self.parameters = parameters
        self.apartments = {}
        self.tenants = {}
        self.transfers = []
        self.bills = []
        self.load_data()

    def load_data(self):
        self.apartments = Apartment.from_json_file(self.parameters.apartments_json_path)
        self.tenants = Tenant.from_json_file(self.parameters.tenants_json_path)
        self.transfers = Transfer.from_json_file(self.parameters.transfers_json_path)
        self.bills = Bill.from_json_file(self.parameters.bills_json_path)

    def get_settlement(self, tenant_key: str, year: int, month: int) -> TenantSettlement:
        tenant = self.tenants[tenant_key]

        apartment_bills = 0
        for bill in self.bills:
            if bill.apartment == tenant.apartment and bill.settlement_year == year and bill.settlement_month == month:
                apartment_bills += bill.amount_pln

        tenants_count = 0
        for other_tenant in self.tenants.values():
            if other_tenant.apartment == tenant.apartment:
                tenants_count += 1.0
        bills_share = apartment_bills / tenants_count

        total_transfers = 0
        for transfer in self.transfers:
            if transfer.tenant == tenant_key and transfer.settlement_year == year and transfer.settlement_month == month:
                total_transfers += transfer.amount_pln

        total_due = tenant.rent_pln + bills_share

        return TenantSettlement(
            tenant=tenant_key, apartment_settlement=f'{tenant.apartment}-{year}-{month:02d}',
            year=year, month=month,
            rent_pln=tenant.rent_pln, bills_pln=bills_share,
            total_due_pln=total_due, total_transfers_pln=total_transfers,
            balance_pln=total_transfers - total_due,
        )

if __name__ == '__main__':
    parameters = Parameters()
    manager = Manager(parameters)
    print("\nApartments:")
    for apartment in manager.apartments.values():
        print(apartment.key, apartment.name, apartment.location, apartment.area_m2)
        for room in apartment.rooms.values():
            print('  ', room.name, room.area_m2)

        print("\nBills:")
        for bill in manager.bills:
            if bill.apartment == apartment.key:
                print(bill.amount_pln, bill.date_due, bill.settlement_year, bill.settlement_month, bill.type)

    for tenant in manager.tenants.values():
        print(tenant.name, tenant.apartment, tenant.room, tenant.rent_pln, tenant.deposit_pln, tenant.date_agreement_from, tenant.date_agreement_to)
        for transfer in manager.transfers:
            if transfer.tenant == tenant.name:
                print(transfer.amount_pln, transfer.date, transfer.settlement_year, transfer.settlement_month)

    for tenant_key in manager.tenants:
        print(manager.get_settlement(tenant_key, 2025, 2))