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
- [ ] **to be done in real-time** conversion from 3 fields to 1 field (symbol name, atm_strike, expiry) -->
  (instrument) <kite-tradingsymbol>

11. ## Interactive Order Management (order summary)
    - [x] create the base ui (table)
- [ ] Order management table/with static fields
- [x] Total algo migration to the UI
- [x] Remove white palette from the UI (text color not showing)
- [x] Live PNL integration to the UI (find actually field names used) 
- [x] Check for at-least one kite account (row one)

## Queries
- [x] Parallelization of the order management
- [x] Live PNL Grouping
- [ ] OMS dynamic fields
- [x] set instrument_df_dict['close_position'] = 1 for cancel order
- kite, kite.quote
- iifl, xt.get_quote(instrument,1502,'JSON'), instrument:  [{'exchangeSegment': 1, 'exchangeInstrumentID': int(res2['ExchangeInstrumentID'])}]
  - res2['ExchangeInstrumentID'] get from iifl instrument file
- [ ] stop and start strategy not working, because of the get_live_ticks functions are still alive (how to get control?)

12. Pending Tasks:
- [ ] Fixing orderbook page update (tradexcb)
- [ ] Fix process terminate issue (tradexcb)
- [ ] Upload OHLC data to MYSQL instead of sqlite3 (api)
- [ ] Add filter logic and candle building logic to API (api)
- [ ] Prepare iDelta (cli) for testing with api connection (idelta+api)
- [ ] SL and Target fields are mandatory.
