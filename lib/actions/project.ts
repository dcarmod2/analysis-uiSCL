import {stringify} from 'querystring'
import {createAction} from 'redux-actions'

import {API} from 'lib/constants'
import selectCurrentProject from 'lib/selectors/current-project'

import fetch from './fetch'
import getFeedsRoutesAndStops from './get-feeds-routes-and-stops'
import {
  saveToServer as saveModification,
  getForProject as getModificationsForProject
} from './modifications'

import {loadBundle} from './'

const PROJECT_URL = API.Project

// project stuff
const addProject = createAction('add project')
export const create = ({bundleId, name, regionId}) =>
  fetch({
    url: PROJECT_URL,
    options: {
      body: {
        bundleId,
        name,
        regionId,
        variants: ['Default']
      },
      method: 'post'
    },
    next: (response) => addProject(response.value)
  })

const deleteLocally = createAction('delete project')
export const deleteProject = (projectId) =>
  fetch({
    options: {
      method: 'delete'
    },
    url: `${PROJECT_URL}/${projectId}`,
    next: () => deleteLocally(projectId)
  })

export const loadProject = (_id) =>
  fetch({
    url: `${PROJECT_URL}/${_id}`,
    next: (r) => set(r.value)
  })

export const loadProjectAndModifications = (_id) => async (dispatch) => {
  const r1 = await Promise.all([
    dispatch(loadProject(_id)),
    dispatch(getModificationsForProject(_id))
  ])
  const project = r1[0]
  const modifications = r1[1]

  const r2 = await Promise.all([
    dispatch(loadBundle(project.bundleId)),
    dispatch(
      getFeedsRoutesAndStops({
        bundleId: project.bundleId,
        forceCompleteUpdate: true,
        modifications
      })
    )
  ])

  return {bundle: r2[0], feeds: r2[1], modifications, project}
}

export const saveToServer = (project) =>
  fetch({
    url: `${PROJECT_URL}/${project._id}`,
    options: {
      body: project,
      method: 'put'
    },
    next: (response) => set(response.value)
  })
export const set = createAction('set project')
export const setAll = createAction('set projects')
export const loadProjects = (query = {}) =>
  fetch({
    url: `${PROJECT_URL}?${stringify(query)}`,
    next: (response) => setAll(response.value)
  })

/**
 * Project Variants
 */
export const createVariant = (name) => (dispatch, getState) => {
  const project = selectCurrentProject(getState())
  const {variants} = project
  return dispatch(
    saveToServer({
      ...project,
      variants: [...variants, name]
    })
  )
}

/**
 * Create a new scenario with all of the same modifications,
 */
export const copyScenario = (index) => async (dispatch, getState) => {
  const state = getState()
  const project = selectCurrentProject(state)
  const {modifications} = state.project

  const newScenarioName = project.variants[index] + ' (copy)'
  const oldLength = project.variants.length

  await dispatch(
    saveToServer({
      ...project,
      variants: [...project.variants, newScenarioName]
    })
  )

  return Promise.all(
    modifications.map((m) => {
      const variants = m.variants
      // Could come from a bitset on the Java side so may be of varying length
      for (let i = 0; i < oldLength; i++) {
        if (variants[i] === undefined) variants[i] = false
      }

      return dispatch(
        saveModification({
          ...m,
          variants: [
            ...variants,
            variants[index] // add the new variant
          ]
        })
      )
    })
  )
}

export const deleteVariant = (index) => async (dispatch, getState) => {
  const state = getState()
  const project = selectCurrentProject(state)
  const {modifications} = state.project

  await dispatch(
    saveToServer({
      ...project,
      variants: project.variants.filter((_, i) => i !== index)
    })
  )

  return Promise.all(
    modifications.map((m) =>
      dispatch(
        saveModification({
          ...m,
          variants: m.variants.filter((_, i) => i !== index)
        })
      )
    )
  )
}

export const editVariantName = ({index, name}) => (dispatch, getState) => {
  const project = selectCurrentProject(getState())
  return dispatch(
    saveToServer({
      ...project,
      variants: project.variants.map((value, i) => (i === index ? name : value))
    })
  )
}
