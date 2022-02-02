import {Alert, AlertIcon, Box, Button, Heading, Stack} from '@chakra-ui/core'
import {useSelector} from 'react-redux'

import {DEFAULT_SEGMENT_SPEED} from 'lib/constants/timetables'
import selectSegmentDistances from 'lib/selectors/segment-distances'
import {create as createTimetable} from 'lib/utils/timetable'

import CopyTimetable from './copy-timetable'
import TimetableComponent from './timetable'

export default function Timetables({
  modification,
  modificationStops,
  numberOfStops,
  timetables,
  update
}) {
  const segmentDistances = useSelector(selectSegmentDistances)

  /** add a timetable */
  const _create = () => {
    const length = timetables.length
    const speeds =
      length > 0
        ? timetables[0].segmentSpeeds
        : segmentDistances.map(() => DEFAULT_SEGMENT_SPEED)
    update({
      timetables: [...timetables, createTimetable(speeds, length)]
    })
  }

  const _createFromOther = (timetable) => {
    update({
      timetables: [...timetables, timetable]
    })
  }

  /** update a timetable */
  const _update = (index, newTimetableProps) => {
    const newTimetables = [...timetables]
    newTimetables[index] = {
      ...timetables[index],
      ...newTimetableProps
    }
    update({timetables: newTimetables})
  }

  const _remove = (index) => {
    const newTimetables = [...timetables]
    newTimetables.splice(index, 1)
    update({timetables: newTimetables})
  }

  return (
    <Stack spacing={4}>
      <Heading size='md'>Timetables ({timetables.length})</Heading>
      {timetables.length === 0 && (
        <Alert status='error'>
          <AlertIcon /> Modification needs at least 1 timetable
        </Alert>
      )}
      <Button
        isFullWidth
        leftIcon='small-add'
        onClick={_create}
        variantColor='green'
      >
        Add new timetable
      </Button>
      <Box>
        <CopyTimetable
          create={_createFromOther}
          intoModification={modification}
        />
      </Box>

      {timetables.map((tt, i) => (
        <TimetableComponent
          key={`timetable-${i}`}
          modificationStops={modificationStops}
          numberOfStops={numberOfStops}
          remove={() => _remove(i)}
          segmentDistances={segmentDistances}
          timetable={tt}
          update={(timetable) => _update(i, timetable)}
        />
      ))}
    </Stack>
  )
}
