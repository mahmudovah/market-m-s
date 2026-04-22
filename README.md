# Bozor Boshqaruv Tizimi (Django)

Ushbu loyiha bozor do'koni va ombori uchun modul struktura bilan yozildi:

- `toifa`: toifalar, mahsulotlar, narx tarixi
- `ombor`: kirim/chiqim harakatlari, yuk qabuli, tannarx hisobi
- `kassa`: do'kon/shaxsiy pul harakatlari, o'tkazmalar, oyma-oy solishtirish
- `qarzdor`: qarzdorlar ro'yxati, qarz va qaytimlar, muddati o'tganlar
- `profil`: do'kon profili, xavfsizlik PIN, eksport log

## Ishga tushirish

```powershell
.\venv\Scripts\python.exe manage.py migrate
.\venv\Scripts\python.exe manage.py createsuperuser
.\venv\Scripts\python.exe manage.py runserver
```

## API nuqtalari

- `/api/` asosiy modul xaritasi
- `/api/toifa/`
- `/api/toifa/products/`
- `/api/toifa/price-history/`
- `/api/ombor/`
- `/api/ombor/stock/`
- `/api/ombor/movements/`
- `/api/ombor/receipt-cost/`
- `/api/kassa/`
- `/api/kassa/accounts/`
- `/api/kassa/monthly-compare/`
- `/api/qarzdor/`
- `/api/qarzdor/debts/`
- `/api/qarzdor/reminders/`
- `/api/profil/`

## Web sahifalar

- `/` bosh dashboard
- `/toifa/`
- `/ombor/`
- `/kassa/`
- `/qarzdor/`
- `/profil/`

## Admin

Admin panelda barcha modellar ro'yxatdan o'tkazilgan:

- `Category`, `Product`, `ProductPriceHistory`
- `WarehouseReceipt`, `WarehouseReceiptItem`, `StockMovement`
- `CashAccount`, `CashTransaction`, `CashTransfer`
- `Debtor`, `Debt`, `DebtPayment`
- `ShopProfile`, `SecuritySetting`, `ExportLog`
