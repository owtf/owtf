import getMuiTheme from 'material-ui/styles/getMuiTheme';
export const TARGET_URL = '/api/targets/search/'
export const TRANSACTIONS_URL = '/api/targets/target_id/transactions/search/'
export const TRANSACTION_HEADER_URL = '/api/targets/target_id/transactions/transaction_id/'
export const TRANSACTION_API_URL = '/api/targets/target_id/transactions/'
export const TRANSACTION_ZCONSOLE_URL = '/ui/targets/target_id/transactions/zconsole'

export const muiTheme = getMuiTheme({
    palette: {
        primary1Color: '#2f4050'
    }
});
