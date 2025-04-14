/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export type Order = {
    symbol?: string;
    status?: number;
    side?: number;
    type?: number;
    price?: number;
    exchange_id?: string;
    id?: string;
    client_order_id?: string | null;
    info?: Record<string, any> | null;
    ledger_id?: string;
    asset_a?: string | null;
    asset_b?: string | null;
    timestamp?: string | null;
    datetime?: string | null;
    time_in_force?: string | null;
    post_only?: boolean | null;
    last_trade_timestamp?: string | null;
    stop_price?: number | null;
    trigger_price?: number | null;
    cost?: number | null;
    amount?: number;
    filled?: number | null;
    remaining?: number | null;
    fee?: number | null;
    average?: number | null;
    trades?: Array<any> | null;
    fees?: Array<any> | null;
    last_update_timestamp?: string | null;
    reduce_only?: boolean | null;
    take_profit_price?: number | null;
    stop_loss_price?: number | null;
};

