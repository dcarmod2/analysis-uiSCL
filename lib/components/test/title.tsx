import {Box, Button, Flex, Heading, Text} from '@chakra-ui/core'
import {faChartArea} from '@fortawesome/free-solid-svg-icons'
import get from 'lodash/get'
import {useDispatch, useSelector,useStore} from 'react-redux'
//import snakeCase from 'lodash/snakeCase'
import {
  //fetchTravelTimeSurface,
  setIsochroneFetchStatus,
  fetchTTSAndDownload
} from 'lib/actions/analysis'
import {abortFetch} from 'lib/actions/fetch'
import {FETCH_TRAVEL_TIME_SURFACE} from 'lib/constants'
import message from 'lib/message'
import {activeOpportunityDataset} from 'lib/modules/opportunity-datasets/selectors'
import selectCurrentProject from 'lib/selectors/current-project'
import selectProfileRequestHasChanged from 'lib/selectors/profile-request-has-changed'
import selectIsochrone from 'lib/selectors/isochrone'
//import downloadJson from 'lib/utils/download-json'
import selectMaxTripDurationMinutes from 'lib/selectors/max-trip-duration-minutes'
//import origins from './origins.json'

import Icon from '../icon'

const getIsochrone = (state) => selectIsochrone(state)

function TitleMessage({fetchStatus, project}) {
  const opportunityDataset = useSelector(activeOpportunityDataset)
  const isochrone = useSelector(selectIsochrone)
  const profileRequestHasChanged = useSelector(selectProfileRequestHasChanged)

  let title = 'Analyze results'
  if (fetchStatus) title = fetchStatus
  else if (!project) title = 'Select a project'
  else if (!isochrone) title = 'Compute travel time'
  else if (profileRequestHasChanged)
    title = 'Results are out of sync with settings'
  else if (!opportunityDataset)
    title = 'Select an opportunity dataset to see accessibility'
  return <Text> {title}</Text>
}

export default function AnalysisTitle() {
  const dispatch = useDispatch()
  const cutoff = useSelector(selectMaxTripDurationMinutes)
  const store = useStore()
  const isochroneFetchStatus = useSelector((s) =>
    get(s, 'analysis.isochroneFetchStatus')
  )
  const currentProject = useSelector(selectCurrentProject)
  const isFetchingIsochrone = !!isochroneFetchStatus

  function abort() {
    dispatch(abortFetch({type: FETCH_TRAVEL_TIME_SURFACE}))
    dispatch(setIsochroneFetchStatus(false))
  }
  
  return (
    <Flex
      align='center'
      borderBottom='1px solid #E2E8F0'
      justify='space-between'
      px={5}
      py={4}
      width='640px'
    >
      <Heading alignItems='center' display='flex' size='md'>
        <Box mr={2}>
          <Icon icon={faChartArea} />
        </Box>
        <TitleMessage
          fetchStatus={isochroneFetchStatus}
          project={currentProject}
        />
      </Heading>
      {isFetchingIsochrone ? (
        <Button rightIcon='small-close' onClick={abort} variantColor='red'>
          Abort
        </Button>
      ) : (
        <Button
          isDisabled={!currentProject}
          rightIcon='repeat'
          onClick={() => dispatch(fetchTTSAndDownload())}
          variantColor='blue'
          title={
            !currentProject
              ? message('analysis.disableFetch')
              : message('analysis.refresh')
          }
        >
          {message('analysis.refresh')}
        </Button>
      )}
    </Flex>
  )
}
