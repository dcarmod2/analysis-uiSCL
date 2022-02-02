import get from 'lodash/get'
import {createSelector} from 'reselect'

export default createSelector(
  (state) => get(state, 'analysis.requestsSettings[1].projectId'),
  (state) => get(state, 'project.projects'),
  (comparisonProjectId, projects = []) =>
    projects.find((s) => s._id === comparisonProjectId)
)
