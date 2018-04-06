/**
 * Combine all sags in this file and export the combined sagas.
 */

import { all } from 'redux-saga/effects';
import sessionSaga from 'containers/Sessions/saga';

export default function* rootSaga() {
  yield all([
    sessionSaga()
  ])
}
