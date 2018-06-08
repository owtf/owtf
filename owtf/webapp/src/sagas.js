/**
 * Combine all sags in this file and export the combined sagas.
 */

import { all } from 'redux-saga/effects';
import sessionSaga from 'containers/Sessions/saga';
import configurationSaga from 'containers/SettingsPage/saga';
import targetSaga from './containers/Transactions/saga';

export default function* rootSaga() {
  yield all([
    configurationSaga(),
    sessionSaga(),
    targetSaga(),
  ])
}
