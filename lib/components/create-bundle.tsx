import {
  Alert,
  AlertDescription,
  AlertIcon,
  AlertTitle,
  Button,
  FormControl,
  FormLabel,
  Heading,
  Input,
  Select,
  Stack,
  Tab,
  Tabs,
  TabList,
  TabPanel,
  TabPanels,
  Text
} from '@chakra-ui/core'
import {faDatabase} from '@fortawesome/free-solid-svg-icons'
import {useRouter} from 'next/router'
import {useState} from 'react'
import {useDispatch, useSelector} from 'react-redux'

import {addBundle} from 'lib/actions'
import fetch from 'lib/actions/fetch'
import {API} from 'lib/constants'
import message from 'lib/message'
import {routeTo} from 'lib/router'
import selectBundles from 'lib/selectors/bundles'
import selectCurrentRegion from 'lib/selectors/current-region'

import Code from './code'
import Icon from './icon'
import InnerDock from './inner-dock'
import DocsLink from './docs-link'

// how often to poll when waiting for a bundle to be read on the server.
const POLL_TIMEOUT_MS = 10000
const STATUS_DONE = 'DONE'
const STATUS_ERROR = 'ERROR'

/**
 * Create bundle form.
 */
export default function CreateBundle() {
  const dispatch = useDispatch<any>()
  const router = useRouter()
  const bundles = useSelector(selectBundles)
  const region = useSelector(selectCurrentRegion)

  const hasExistingBundles = bundles.length > 0
  const [reuseOsm, setReuseOsm] = useState(hasExistingBundles)
  const [reuseGtfs, setReuseGtfs] = useState(hasExistingBundles)
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState<string | void>()
  const [formData, setFormData] = useState<Record<string, string>>({
    name: ''
  })
  const onChange = (propName: string) => (e) => {
    // Since `target` will not exist if used in the function call below, extract
    // value first.
    const value = e.target.value
    setFormData((d) => ({...d, [propName]: value}))
  }

  const isValid = () =>
    formData.name &&
    ((reuseOsm && formData.osmId) || (!reuseOsm && formData.osm)) &&
    ((reuseGtfs && formData.feedGroupId) || (!reuseGtfs && formData.feedGroup))

  const regionId = region._id
  const bounds = region.bounds

  /**
   * Check if the upload has completed
   */
  function checkUploadState(_id: string) {
    dispatch(fetch({url: `${API.Bundle}/${_id}`}))
      .then((bundle) => {
        if (bundle.status === STATUS_DONE) {
          // Add bundle to the store
          dispatch(addBundle(bundle))

          // Go to bundle list
          const {href, as} = routeTo('bundleEdit', {bundleId: _id, regionId})
          router.push(href, as)
        } else if (bundle.status === STATUS_ERROR) {
          setUploading(false)
          setError(bundle.statusText)
        } else {
          setUploading(bundle.status)
          setTimeout(() => checkUploadState(_id), POLL_TIMEOUT_MS)
        }
      })
      .catch(() => {
        // this request failing does not imply that the bundle failed to upload
        setTimeout(() => checkUploadState(_id), POLL_TIMEOUT_MS)
      })
  }

  function submit(e) {
    // don't submit the form
    e.preventDefault()

    const body = new window.FormData(e.target)

    if (reuseGtfs) body.delete('feedGroup')
    else body.delete('feedGroupId')

    if (reuseOsm) body.delete('osm')
    else body.delete('osmId')

    if (isValid()) {
      setUploading(true)
      setError()

      dispatch(
        fetch({
          url: API.Bundle,
          options: {body, method: 'post'}
        })
      )
        .then((bundle) => {
          setTimeout(() => checkUploadState(bundle._id), POLL_TIMEOUT_MS)
        })
        .catch(() => setUploading(false))
    }
  }

  return (
    <InnerDock style={{width: '640px'}}>
      <Stack p={8} spacing={8}>
        <Heading size='lg'>
          <Icon icon={faDatabase} /> {message('bundle.create')}
        </Heading>

        <Text>{message('bundle.createDescription')}</Text>

        {uploading && (
          <Alert status='info'>
            <AlertIcon />
            <Stack spacing={2}>
              <AlertTitle>{message('bundle.processing')}</AlertTitle>
              <AlertDescription>{uploading}</AlertDescription>
            </Stack>
          </Alert>
        )}

        {error && (
          <Alert status='error'>
            <AlertIcon /> {error}
          </Alert>
        )}

        {!uploading && !error && (
          <Alert status='info'>
            <AlertIcon />
            {message('bundle.notice')}
          </Alert>
        )}
      </Stack>

      <Stack
        as='form'
        onSubmit={submit}
        opacity={uploading ? 0.4 : 1}
        pointerEvents={uploading ? 'none' : 'auto'}
        pl={8}
        pr={8}
        spacing={8}
      >
        <FormControl isRequired isInvalid={formData.name.length < 1}>
          <FormLabel htmlFor='bundleName'>{message('bundle.name')}</FormLabel>
          <Input
            id='bundleName'
            name='bundleName'
            onChange={onChange('name')}
            placeholder='Name'
          />
        </FormControl>

        <Tabs
          defaultIndex={hasExistingBundles ? 0 : 1}
          isFitted
          onChange={(i) => setReuseOsm(i === 0)}
        >
          <TabList>
            <Tab
              aria-disabled={!hasExistingBundles}
              disabled={!hasExistingBundles}
            >
              {message('bundle.osm.existingTitle')}
            </Tab>
            <Tab>{message('bundle.osm.uploadNewTitle')}</Tab>
          </TabList>

          <TabPanels>
            <TabPanel pt={4}>
              {reuseOsm && (
                <Select
                  id='osmId'
                  name='osmId'
                  onChange={onChange('osmId')}
                  placeholder={message('bundle.osm.existingLabel')}
                >
                  {bundles.map((b) => (
                    <option key={b._id} value={b.osmId}>
                      {b.name}
                    </option>
                  ))}
                </Select>
              )}
            </TabPanel>
            <TabPanel>
              {!reuseOsm && (
                <Stack spacing={4} pt={4}>
                  <FormControl isRequired>
                    <FormLabel htmlFor='osm'>
                      {message('bundle.osm.uploadNewLabel')}
                    </FormLabel>
                    <Input
                      accept='.pbf'
                      id='osm'
                      name='osm'
                      type='file'
                      onChange={onChange('osm')}
                    />
                  </FormControl>
                </Stack>
              )}
            </TabPanel>
          </TabPanels>
        </Tabs>

        <Tabs
          defaultIndex={hasExistingBundles ? 0 : 1}
          isFitted
          onChange={(i) => setReuseGtfs(i === 0)}
        >
          <TabList>
            <Tab
              aria-disabled={!hasExistingBundles}
              disabled={!hasExistingBundles}
            >
              {message('bundle.gtfs.existingTitle')}
            </Tab>
            <Tab>{message('bundle.gtfs.uploadNewTitle')}</Tab>
          </TabList>

          <TabPanels>
            <TabPanel pt={4}>
              {reuseGtfs && (
                <Select
                  id='feedGroupId'
                  name='feedGroupId'
                  onChange={onChange('feedGroupId')}
                  placeholder={message('bundle.gtfs.existingLabel')}
                >
                  {bundles.map((b) => (
                    <option key={b._id} value={b.feedGroupId}>
                      {b.name}
                    </option>
                  ))}
                </Select>
              )}
            </TabPanel>
            <TabPanel pt={4}>
              {!reuseGtfs && (
                <FormControl isRequired>
                  <FormLabel htmlFor='feedGroup'>
                    {message('bundle.gtfs.uploadNewLabel')}
                  </FormLabel>
                  <Input
                    accept='.zip'
                    id='feedGroup'
                    multiple
                    name='feedGroup'
                    onChange={onChange('feedGroup')}
                    type='file'
                  />
                </FormControl>
              )}
            </TabPanel>
          </TabPanels>
        </Tabs>

        <input type='hidden' name='regionId' value={regionId} />

        <Stack spacing={4}>
          <Button
            isDisabled={!isValid()}
            isLoading={uploading}
            leftIcon='check'
            loadingText={message('common.processing')}
            size='lg'
            type='submit'
            variantColor='green'
          >
            {message('common.create')}
          </Button>
        </Stack>
      </Stack>
    </InnerDock>
  )
}
