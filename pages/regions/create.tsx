import {
  Alert,
  Button,
  FormControl,
  FormLabel,
  Heading,
  Input,
  Stack,
  useToast
} from '@chakra-ui/core'
import {faMap} from '@fortawesome/free-solid-svg-icons'
import dynamic from 'next/dynamic'
import {useState} from 'react'

import EditBoundsForm from 'lib/components/edit-bounds-form'
import Icon from 'lib/components/icon'
import InnerDock from 'lib/components/inner-dock'
import {SPACING_FORM} from 'lib/constants/chakra'
import {DEFAULT_BOUNDS} from 'lib/constants/region'
import useInput from 'lib/hooks/use-controlled-input'
import useRouteTo from 'lib/hooks/use-route-to'
import MapLayout from 'lib/layouts/map'
import message from 'lib/message'
import {postJSON} from 'lib/utils/safe-fetch'
import reprojectCoordinates from 'lib/utils/reproject-coordinates'

const EditBounds = dynamic(() => import('lib/components/map/edit-bounds'), {
  ssr: false
})

/// Name cannot be empty
const testName = (n) => n && n.length > 0

/**
 * Create a region.
 */
export default function CreateRegionPage() {
  const [error, setError] = useState<void | string>()
  const goToProjects = useRouteTo('projects')
  const [uploading, setUploading] = useState(false)
  const [bounds, setBounds] = useState(DEFAULT_BOUNDS)
  const toast = useToast()

  const nameInput = useInput({test: testName, value: ''})
  const descriptionInput = useInput({value: ''})

  // Create/save will keep checking load status and redirect to the region page
  async function _create() {
    const nw = reprojectCoordinates({lat: bounds.north, lon: bounds.west})
    const se = reprojectCoordinates({lat: bounds.south, lon: bounds.east})
    const b = {north: nw.lat, west: nw.lon, south: se.lat, east: se.lon}

    // Validate the bounds
    const boundsIsNaN =
      isNaN(b.north) || isNaN(b.south) || isNaN(b.east) || isNaN(b.west)
    if (boundsIsNaN) {
      setError('Bounds must be valid coordinates.')
      return
    }

    setUploading(true)

    const res = await postJSON('/api/db/regions', {
      name: nameInput.value,
      description: descriptionInput.value,
      bounds
    })

    if (res.ok) {
      goToProjects({regionId: (res.data as CL.Region)._id})
      toast({
        title: 'Region created',
        position: 'top',
        status: 'success'
      })
    } else {
      setUploading(false)
      setError((res.data as Error).message)
    }
  }

  return (
    <InnerDock>
      <EditBounds bounds={bounds} save={setBounds} />

      <Stack as='form' p={SPACING_FORM} spacing={SPACING_FORM}>
        <Heading size='md'>
          <Icon icon={faMap} /> <span> {message('region.createAction')}</span>
        </Heading>

        {error && <Alert status='error'>{error}</Alert>}

        <FormControl
          isDisabled={uploading}
          isRequired
          isInvalid={nameInput.isInvalid}
        >
          <FormLabel htmlFor={nameInput.id}>{message('region.name')}</FormLabel>
          <Input {...nameInput} placeholder={message('region.name')} />
        </FormControl>

        <FormControl isDisabled={uploading}>
          <FormLabel htmlFor={descriptionInput.id}>
            {message('region.description')}
          </FormLabel>
          <Input
            {...descriptionInput}
            placeholder={message('region.description')}
          />
        </FormControl>

        <EditBoundsForm
          bounds={bounds}
          isDisabled={uploading}
          onChange={(d, v) => setBounds((b) => ({...b, [d]: v}))}
        />

        <Button
          isFullWidth
          isDisabled={nameInput.isInvalid}
          isLoading={uploading}
          leftIcon='check'
          loadingText='Creating region...'
          onClick={_create}
          size='lg'
          variantColor='green'
        >
          {message('region.createAction')}
        </Button>
      </Stack>
    </InnerDock>
  )
}

// Add MapLayout
CreateRegionPage.Layout = MapLayout
