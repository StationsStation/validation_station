/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { StateResponse } from '../models/StateResponse';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class DefaultService {
    /**
     * Get current portfolio and market state
     * @returns StateResponse Current state including portfolio, prices, and orders
     * @throws ApiError
     */
    public static getState(): CancelablePromise<StateResponse> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/',
        });
    }
}
