/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export type Price = {
    symbol?: string;
    /**
     * Unix timestamp in milliseconds
     */
    timestamp?: number;
    datetime?: string;
    ask?: number;
    bid?: number;
    asset_a?: string | null;
    asset_b?: string | null;
    bid_volume?: number | null;
    ask_volume?: number | null;
    high?: number;
    low?: number;
    vwap?: number | null;
    open?: number | null;
    close?: number | null;
    last?: number | null;
    previous_close?: number | null;
    change?: number | null;
    percentage?: number | null;
    average?: number | null;
    base_volume?: number | null;
    quote_volume?: number | null;
    info?: Record<string, any> | null;
};

