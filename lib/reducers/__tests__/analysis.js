import {handleActions} from 'redux-actions'

import * as analysis from '../analysis'
import {mockScenarioApplicationError} from '../../utils/mock-data'

describe('reducers > analysis', () => {
  const reducer = handleActions(analysis.reducers, analysis.initialState)

  // Default State Test
  it('should handle default state', () => {
    expect(reducer(undefined, {type: 'blah', payload: {}})).toMatchSnapshot()
  })

  // Specific Handler Tests
  it('should handle update profile request', () => {
    const action = {
      type: 'update profile request',
      payload: {
        fromTime: 24321,
        toTime: 25220
      }
    }

    expect(reducer(undefined, action)).toMatchSnapshot()
  })

  it('should handle set isochrone cutoff', () => {
    const action = {type: 'set isochrone cutoff', payload: 123}
    expect(reducer(undefined, action)).toMatchSnapshot()
  })

  it('should handle set isochrone fetch status', () => {
    const action = {type: 'set isochrone fetch status', payload: true}
    expect(reducer(undefined, action)).toMatchSnapshot()
  })

  it('should handle set scenario application errors', () => {
    const action = {
      type: 'set scenario application errors',
      payload: [mockScenarioApplicationError]
    }
    expect(reducer(undefined, action)).toMatchSnapshot()
  })

  it('should handle enter analysis mode', () => {
    const action = {type: 'enter analysis mode'}
    expect(reducer(undefined, action)).toMatchSnapshot()
  })

  it('should handle exit analysis mode', () => {
    const action = {type: 'exit analysis mode'}
    expect(reducer(undefined, action)).toMatchSnapshot()
  })

  it('should handle set active regional analyses', () => {
    const action = {
      type: 'set active regional analyses',
      payload: {
        _id: 'project id',
        comparisonId: 'comparison id'
      }
    }

    expect(reducer(undefined, action)).toMatchSnapshot()
  })

  it('should handle set regional analysis grids', () => {
    const action = {
      type: 'set regional analysis grids',
      payload: {
        grid: {which: 'GRID'},
        comparisonGrid: {which: 'COMPARISON GRID'},
        differenceGrid: {which: 'DIFFERENCE_GRID'},
        probabilityGrid: {which: 'PROBABILITY GRID'}
      }
    }

    expect(reducer(undefined, action)).toMatchSnapshot()
  })
})
