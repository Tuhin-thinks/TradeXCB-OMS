## Completed:
- [x] Sorting of Expiry dates
- [x] Saving and Loading of trading Symbol Mapping
- [x] Created base UI for Multi-Account-Details
- [x] create the base ui (table based)
- [x] stockbroker option as a drop-down
- [x] no. of lots show at the end
- [x] Name column as [identifier]
- [x] Add a button to add a new row
- [x] Add a button to delete a row (context-event)
- [x] All fields should be hidden
- [x] Add a button to save the data to excel
- [x] Change Logo
- [x] Fixing orderbook page update (tradexcb)
- [x] Fix process terminate issue (tradexcb)
- [x] Upload OHLC data to MYSQL instead of sqlite3 (api)
- [x] Add filter logic and candle building logic to API (api)
- [x] **to be done in real-time** conversion from 3 fields to 1 field (symbol name, atm_strike, expiry) -->
  (instrument) <kite-tradingsymbol>
- [x] create the base ui (table)
- [x] Order management table/with static fields
- [x] Total algo migration to the UI
- [x] Remove white palette from the UI (text color not showing)
- [x] Live PNL integration to the UI (find actually field names used) 
- [x] Check for at-least one kite account (row one)
- [x] Live PNL Grouping
- [x] OMS dynamic fields
- [x] set instrument_df_dict['close_position'] = 1 for cancel order
- kite, kite.quote
- iifl, xt.get_quote(instrument,1502,'JSON'), instrument:  [{'exchangeSegment': 1, 'exchangeInstrumentID': int(res2['ExchangeInstrumentID'])}]
- res2['ExchangeInstrumentID'] get from iifl instrument file
- [x] stop and start strategy not working, because of the get_live_ticks functions are still alive (how to get control?)
- [x] Remove extra characters after paste (newline, tab-space, etc).
- [x] popup dialog for order status.

## Queries
- [ ] Parallelization of the order management

12. Pending Tasks:

### Current Issues:
- [ ] store order status string in a datastructure for all active order ids.
- [ ] place/cancel orders parallelized.
- [ ] login test after login credentials are added.

*[24 July, 2022]*
- [ ] when few logs comes at the same point of time, last log is not displayed. #fix-this
  - Whenever one user main order status is not 'COMPLETE' then :
    - don't place SL order.
- [ ] things need to do to fix (a):
  - [ ] create a class of user.
  - [ ] embed all algo logic inside user's class.
  - [ ] create unique id with timestamp and instrument and username. (1646844654_NIFTY22JULFUT_ABC)
- [ ] Check if master account login  is success, else exit algo process.
  - [ ] Try login to all accounts, whichever fails, delete that user from user list.
    (this user won't be user for rest part of the algorithm).
  - [ ] Whenever one user main order status is not 'COMPLETE' then :
  don't place SL order.
- Order Status Page:
  - [ ] create each row in **"Order Management"** table w.r.t. user x instrument times.
    ex. there are 10 users
    and 12 rows in trading symbol mapping table, then there'll be 10x12 = 120 rows (for all valid user accounts)
- [x] remove iifl
- [ ] remove alice blue
