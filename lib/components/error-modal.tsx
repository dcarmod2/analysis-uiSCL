import {
  Box,
  Button,
  Collapse,
  Icon,
  Link,
  List,
  ListItem,
  Modal,
  ModalBody,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalCloseButton,
  ModalFooter,
  Stack,
  Text
} from '@chakra-ui/core'
import get from 'lodash/get'
import {useState} from 'react'

import message from 'lib/message'

const ExternalLink = ({children, href}) => (
  <Link isExternal color='blue.500' href={href}>
    {children} <Icon name='external-link' mx='2px' />
  </Link>
)

function StackTrace({stackTrace, ...p}) {
  // Hide the stack trace in production
  const [show, setShow] = useState(process.env.NODE_ENV !== 'production')
  const handleToggle = () => setShow((show) => !show)

  return (
    <Stack spacing={4} {...p}>
      <Button onClick={handleToggle} variantColor='blue'>
        {show ? 'Hide' : 'Show'} stack trace
      </Button>
      <Collapse
        borderRadius='2px'
        fontFamily='mono'
        isOpen={show}
        overflowX='scroll'
        whiteSpace='pre'
        padding={2}
        backgroundColor='#333'
        color='#fff'
      >
        {stackTrace}
      </Collapse>
    </Stack>
  )
}

function createMailToFromError(url, stack) {
  let mailto = `mailto:${message(
    'error.supportEmail'
  )}?subject=Conveyal Error&body=`
  mailto += encodeURIComponent(url || get(window, 'location.href'))
  if (stack) mailto += encodeURIComponent(`${stack}`.substring(0, 350))
  return mailto
}

export default function ErrorModal({
  clear,
  error,
  title = message('error.title')
}) {
  const errorMessage = typeof error === 'string' ? error : error.message
  const stack = error.stack

  return (
    <Modal
      closeOnOverlayClick={false}
      isOpen={error}
      onClose={() => clear()}
      size='2xl'
    >
      <ModalOverlay />
      <ModalContent borderRadius='4px'>
        <ModalHeader>{title}</ModalHeader>
        <ModalCloseButton />
        <ModalBody>
          <Stack spacing={4}>
            <Text>{errorMessage}</Text>
            {error.url && <Text>{error.url}</Text>}
            {stack && <StackTrace stackTrace={stack} />}
            <Box>
              {message('error.report') + ' '}
              <ExternalLink href={createMailToFromError(error.url, stack)}>
                {message('error.supportEmail')}.
              </ExternalLink>
            </Box>
            <List styleType='disc'>
              <ListItem>
                <ExternalLink href='https://support.apple.com/en-us/HT201361'>
                  How to take a screenshot on a Mac
                </ExternalLink>
              </ListItem>
              <ListItem>
                <ExternalLink href='https://www.howtogeek.com/226280/how-to-take-screenshots-in-windows-10/'>
                  How to take a screenshot on a PC
                </ExternalLink>
              </ListItem>
            </List>
          </Stack>
        </ModalBody>
        <ModalFooter>
          <Button
            leftIcon='arrow-back'
            onClick={() => {
              window.history.back()
              clear()
            }}
            variantColor='yellow'
          >
            {message('error.back')}
          </Button>
        </ModalFooter>
      </ModalContent>
    </Modal>
  )
}
