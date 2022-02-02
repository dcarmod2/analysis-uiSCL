import {createAction} from 'redux-actions'

import {getJSON} from 'lib/utils/safe-fetch'

import {loadProjects} from './project'
import {loadRequestsSettings} from './analysis/profile-request'

import {loadBundles} from './'

export const clear = createAction('clear current region')

export const loadRegion = (id) => async (dispatch) => {
  const res = await getJSON(`/api/db/regions/${id}`)
  if (res.ok) {
    dispatch(setLocally(res.data))
    return res.data
  } else {
    throw res
  }
}

/**
 * Fully load a region and it's associated resources.
 */
export const load = (id) => async (dispatch) => {
  const results = await Promise.all([
    dispatch(loadBundles({regionId: id})),
    dispatch(loadProjects({regionId: id})),
    dispatch(loadRegion(id))
  ])

  // Load and set profile request
  dispatch(loadRequestsSettings(id))

  return {bundles: results[0], projects: results[1], region: results[2]}
}

export const setLocally = createAction('set region')
